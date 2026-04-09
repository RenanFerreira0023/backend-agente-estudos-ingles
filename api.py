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

        def response_generator():
            with model.chat_session():
                prompt = request.prompt
                if file_content and isinstance(file_content, str):
                    prompt = f"Conteúdo do arquivo enviado:\n---\n{file_content}\n---\n\n{prompt}\n---\n\nResponda em portugues do brasil"
                
                logger.info(f"Gerando resposta para prompt: {request.prompt[:50]}...")
                for token in model.generate(
                    prompt,
                    max_tokens=settings.MAX_TOKENS, 
                    temp=settings.TEMPERATURE, 
                    streaming=True
                ):
                    yield token

        return StreamingResponse(response_generator(), media_type="text/plain")
            
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

