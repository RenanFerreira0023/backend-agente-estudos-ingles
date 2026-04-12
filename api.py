from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from gpt4all import GPT4All
from contextlib import asynccontextmanager
import os
import uvicorn
import logging
import sys
import base64
import whisper
import aiofiles
import torch
from typing import Optional
from config import settings
from database import init_db, SessionLocal, User, Session as DBSession, Message
from tools import TOOLS_REGISTRY, TOOLS_DESCRIPTION
import json
import uuid
from tasks import start_scheduler

# ─── Configuração de Logging ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("api")

# ─── Funções Utilitárias ────────────────────────────────────────────────────
def decode_base64(file: str):
    """
    Decodifica uma string base64 (com ou sem cabeçalho) para texto ou bytes.
    """
    try:
        if "," in file:
            header, encoded = file.split(",", 1)
        else:
            encoded = file
        
        decoded_bytes = base64.b64decode(encoded)
        try:
            return decoded_bytes.decode('utf-8')
        except UnicodeDecodeError:
            return decoded_bytes
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao decodificar arquivo base64: {str(e)}")

# ─── Estado Global do Modelo ────────────────────────────────────────────────
state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação: carrega o modelo na inicialização.
    """
    logger.info("🔧 Inicializando Banco de Dados...")
    init_db()
    
    logger.info("⚙️ Acordando Trabalhadores de Fundo (Background Tasks)...")
    start_scheduler()
    
    os.makedirs(settings.MODEL_PATH, exist_ok=True)
    logger.info(f"⏳ Carregando modelo {settings.MODEL_NAME} em {settings.MODEL_PATH}...")
    logger.info(f"🚀 Dispositivo configurado: {settings.DEVICE}")
    
    try:
        state["model"] = GPT4All(
            settings.MODEL_NAME, 
            model_path=settings.MODEL_PATH, 
            allow_download=True, 
            device=settings.DEVICE,
            n_ctx=settings.CONTEXT_SIZE
        )
        logger.info("✅ Modelo carregado com sucesso!")
    except Exception as e:
        logger.critical(f"❌ Erro crítico ao carregar o modelo: {e}")
        if settings.DEVICE == "gpu":
            logger.warning("⚠️ Falha na GPU. Tentando fallback para CPU...")
            try:
                state["model"] = GPT4All(
                    settings.MODEL_NAME, 
                    model_path=settings.MODEL_PATH, 
                    allow_download=True, 
                    device="cpu",
                    n_ctx=settings.CONTEXT_SIZE
                )
                logger.info("✅ Modelo carregado em CPU (Fallback).")
            except Exception as cpu_e:
                logger.critical(f"❌ Falha total ao carregar o modelo: {cpu_e}")
                raise cpu_e
        else:
            raise e
    
    yield
    state.clear()
    logger.info("🛑 Servidor desligado e recursos liberados.")

# ─── Inicialização da APP ───────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME, 
    description=f"API para interação com o modelo {settings.MODEL_NAME}",
    lifespan=lifespan
)

# ─── Middlewares ────────────────────────────────────────────────────────────
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=settings.TRUSTED_HOSTS
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Modelos de Dados ───────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    prompt: str
    file: Optional[str] = None
    session_uuid: Optional[str] = None

class VideoRequest(BaseModel):
    video_base64: str
    filename: str

# ─── Rotas ──────────────────────────────────────────────────────────────────
@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Rota para enviar um prompt ao modelo e receber a resposta via streaming.
    """
    model = state.get("model")
    if not model:
        raise HTTPException(status_code=503, detail="Modelo não inicializado corretamente")

    try:
        file_content = None
        if request.file:
            file_content = decode_base64(request.file)
            logger.info("Arquivo recebido e decodificado.")

        # Garantir que temos um UUID de sessão
        session_uuid = request.session_uuid or str(uuid.uuid4())

        def response_generator(sess_uuid):
            db = SessionLocal()
            try:
                # 1. Configurar Usuário e Sessão
                default_user = db.query(User).filter_by(username="aluno_local").first()
                if not default_user:
                    default_user = User(username="aluno_local")
                    db.add(default_user)
                    db.commit()
                    db.refresh(default_user)
                    
                db_session = db.query(DBSession).filter_by(session_uuid=sess_uuid).first()
                if not db_session:
                    db_session = DBSession(user_id=default_user.id, session_uuid=sess_uuid)
                    db.add(db_session)
                    db.commit()
                    db.refresh(db_session)

                # 2. Salvar Mensagem Atual do Usuário
                user_msg = Message(session_id=db_session.id, role="user", content=request.prompt)
                db.add(user_msg)
                db.commit()

                # 3. Resgatar Histórico Recente (últimas 10 mensagens)
                history = db.query(Message).filter_by(session_id=db_session.id).order_by(Message.created_at.desc()).limit(10).all()
                history.reverse() # Colocar de volta na ordem cronológica de leitura

                # 4. Formatar o Prompt com Injeção de Histórico e Ferramentas
                system_prompt = f"""Você é um professor de inglês proativo. Ensine de forma didática e em português do Brasil, cuidando para dar respostas contextuais.

=== FERRAMENTAS DISPONÍVEIS ===
Você tem acesso a algumas ferramentas. Se precisar utilizar uma (por exemplo, para pesquisar uma palavra ou salvar um flashcard), envie EXATAMENTE o bloco abaixo e PARE de escrever:
<tool_call>
{{"name": "dictionary_lookup", "parameters": {{"word": "apple"}}}}
</tool_call>

{TOOLS_DESCRIPTION}
==============================="""
                
                formatted_prompt = f"System: {system_prompt}\n\n"
                
                # Injetar interações passadas
                for msg in history[:-1]:
                    role_prefix = "User" if msg.role == "user" else "Teacher"
                    formatted_prompt += f"{role_prefix}: {msg.content}\n"
                
                # Prompt atual com arquivo (se houver)
                current_prompt = request.prompt
                if file_content and isinstance(file_content, str):
                    current_prompt = f"[Contexto do Arquivo Enviado]:\n{file_content}\n\n{current_prompt}"
                
                formatted_prompt += f"User: {current_prompt}\nTeacher:"

                logger.info(f"Gerando resposta Agent Loop. Sessão: {sess_uuid}")
                full_response = ""
                
                # 5. Agent Loop (ReAct) com limite de 3 ações autônomas
                iteration = 0
                max_iterations = 3
                
                while iteration < max_iterations:
                    iteration += 1
                    buffer = ""
                    in_tool = False
                    tool_data = ""
                    has_tool = False
                    
                    class ToolCallStopper:
                        def __init__(self):
                            self.buffer = ""
                        def __call__(self, token_id, response):
                            self.buffer += response
                            if "</tool_call>" in self.buffer:
                                return False
                            return True
                    
                    stopper = ToolCallStopper()

                    with model.chat_session():
                        for token in model.generate(
                            formatted_prompt,
                            max_tokens=settings.MAX_TOKENS, 
                            temp=settings.TEMPERATURE, 
                            streaming=True,
                            callback=stopper
                        ):
                            full_response += token
                            buffer += token
                            
                            # Lógica de intercepção de ferramentas durante o Streaming
                            if not in_tool:
                                if "<tool_call>" in buffer:
                                    parts = buffer.split("<tool_call>")
                                    if parts[0]:
                                        yield parts[0]
                                    in_tool = True
                                    buffer = parts[1] if len(parts) > 1 else ""
                                    has_tool = True
                                else:
                                    # Yielding seguro: evita quebrar a tag "<tool_call>" no meio
                                    idx = buffer.rfind("<")
                                    if idx != -1:
                                        chunk = buffer[:idx]
                                        if chunk:
                                            yield chunk
                                        buffer = buffer[idx:]
                                        # Se a tag < encontrada não estiver indo em direção a tool_call, solte-a
                                        if not "<tool_call>".startswith(buffer):
                                            yield buffer
                                            buffer = ""
                                    else:
                                        yield buffer
                                        buffer = ""
                            else:
                                # Estamos dentro do bloco json da tool_call. 
                                # Não mostramos isso para o usuário
                                if "</tool_call>" in buffer:
                                    parts = buffer.split("</tool_call>")
                                    if parts[0] not in tool_data: # Segurança para não duplicar se receber pedaços
                                        tool_data = parts[0] # Pega exatamente o recheio do json
                                    # Em vez de break forçado (que causa erro na memória C++ da placa de vídeo),
                                    # O stopper cuidará de desligar suavemente o motor e esvaziar a fila.
                                    pass
                                else:
                                    tool_data = buffer

                                    
                        if not in_tool and buffer:
                            yield buffer

                    # Avaliar se o loop de LLM invocou uma ferramenta validada
                    if has_tool:
                        t_name = "unknown"
                        try:
                            clean_json_str = tool_data.strip()
                            tool_exec = json.loads(clean_json_str)
                            t_name = tool_exec.get("name", "unknown")
                            t_params = tool_exec.get("parameters", {})
                            
                            logger.info(f"🛠️ Ferramenta acionada: {t_name} | Params: {t_params}")
                            
                            # Injeção de dependência condicional
                            if t_name == "save_flashcard":
                                t_params["user_id"] = default_user.id
                                
                            if t_name in TOOLS_REGISTRY:
                                tool_result = TOOLS_REGISTRY[t_name](**t_params)
                            else:
                                tool_result = f"Error: A ferramenta '{t_name}' não existe."
                                
                        except Exception as e:
                            logger.error(f"Erro ao parsear/executar a ferramenta: {e}")
                            tool_result = f"Error interpreting tool parameters: {str(e)}. Make sure to respond only with standard JSON format."
                            
                        # Informar o modelo sobre o resultado e pedir que ele retome a resposta pedagógica
                        msg_to_add = f"\n[Tool Execution Result ({t_name})]: {tool_result}\nTeacher (continuando):"
                        formatted_prompt += f"\n<tool_call>{tool_data}</tool_call>{msg_to_add}"
                        full_response += f"\n[System Log: executed {t_name} -> {tool_result}]\n"
                        # E roda o 'while' novamente...
                    else:
                        break # Encerrou a resposta normalmente (e atendeu o aluno)

                # 6. Salvar resposta no banco ao finalizar o stream
                assistant_msg = Message(session_id=db_session.id, role="assistant", content=full_response)
                db.add(assistant_msg)
                db.commit()

            except Exception as e:
                logger.error(f"Erro durante gerador de resposta: {e}")
                db.rollback()
            finally:
                db.close()

        headers = {"X-Session-ID": session_uuid}
        # Adicionar Access-Control-Expose-Headers para que o frontend possa ler o atributo Session-ID
        headers["Access-Control-Expose-Headers"] = "X-Session-ID"
        return StreamingResponse(response_generator(session_uuid), media_type="text/plain", headers=headers)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar resposta: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao processar chat")

@app.get("/health")
async def health():
    return {
        "status": "ok" if "model" in state else "error", 
        "model": settings.MODEL_NAME,
        "device_config": settings.DEVICE
    }

@app.post("/uploadVideo")
async def upload_video(request: VideoRequest):
    """
    Recebe um vídeo em base64, transcreve com Whisper e retorna o texto.
    """
    temp_filename = "video_recebido.mp4"
    try:
        video_data = base64.b64decode(request.video_base64)
        async with aiofiles.open(temp_filename, "wb") as f:
            await f.write(video_data)
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"💾 Iniciando transcrição com Whisper ({device.upper()})...")
        whisper_model = whisper.load_model("base", device=device)
        result = whisper_model.transcribe(temp_filename)
        
        return {"text": result["text"].strip()}
        
    except Exception as e:
        logger.error(f"❌ Erro na transcrição de vídeo: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

if __name__ == "__main__":
    logger.info(f"Iniciando {settings.APP_NAME} em {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "api:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=settings.DEBUG
    )

