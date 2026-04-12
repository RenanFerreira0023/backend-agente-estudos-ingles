# 🎓 Backend - Agente de Estudos de Inglês

A API que atua como o "cérebro" de um agente inteligente para ensino de inglês. Desenvolvido com **FastAPI**, ele utiliza o modelo **DeepSeek-R1** rodando localmente para atuar como professor de inglês, incluindo memória persistente e uso autônomo de ferramentas (agente ReAct). Além disso, transcreve vídeos e áudios com o **OpenAI Whisper**.

---

## 🚀 Funcionalidades Principais

- **Professor Autônomo com IA (ReAct):** A IA decide sozinha quando usar ferramentas, como buscar palavras no dicionário ou salvar *flashcards*, tornando a aula mais dinâmica.
- **Persistência e Histórico:** O agente guarda o histórico das aulas (usando o PostgreSQL), permitindo conversas prolongadas sem perder o contexto.
- **Transcrição Multimídia (Whisper):** Endpoint nativo para converter trechos de vídeo ou áudio enviados em texto legível para estudos.
- **Processamento de Arquivos:** Permite aos alunos enviar materiais e textos próprios (via Base64) junto de suas dúvidas.
- **Alta Performance:** Sistema automatizado com suporte a hardware acelerado por placa de vídeo (**GPU**) oferecendo respostas em *streaming*, e com possibilidade de troca para uso de CPU (fallback).

---

## ⚙️ Instalação e Configuração

### 1. Download e Ambiente
```bash
git clone https://github.com/RenanFerreira0023/backend-agente-estudos-ingles.git
cd backend-agente-estudos-ingles

# Crie e ative o ambiente virtual
python -m venv venv

# No Windows
venv\Scripts\activate
# No Linux/Mac: source venv/bin/activate

# Instale os pacotes
pip install -r requirements.txt
```

### 2. Configurando as Variáveis (`.env`)
O projeto exige que você crie um arquivo chamado `.env` na raiz do repositório para realizar sua configuração com facilidade.
Copie o bloco abaixo para dentro do seu `.env` e altere os dados do banco de dados PostgreSQL conforme as suas credenciais de máquina:

```env
# Banco de Dados
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=sua-senha      # <- ALOQUE SUA SENHA AQUI
DB_NAME=super-aluno-ingles # <- Certifique-se de que este banco já exista criado no PostgreSQL

# Hardware
USE_GPU=True               # Se você NÃO tiver placa de vídeo dedicada, deixe False

# Modelos
MODEL_NAME=DeepSeek-R1-Distill-Llama-8B-Q4_0.gguf
CONTEXT_SIZE=8192
```

### 3. Executando a API
Certifique-se de que o **PostgreSQL** está online com o DB criado. Então rode o servidor localmente:
```bash
python api.py
```
A API ficará disponível no seu local em: `http://localhost:8000`.

---

## 🛣️ Integração da API (Principais Rotas)

- **`POST /chat`**: Envia mensagens para o professor, suportando upload de conteúdo anexo e gerando a resposta em forma de escrita sendo recebida em tempo real (*streaming*).
- **`POST /uploadVideo`**: Envio de um arquivo de vídeo (base64) para extração de áudio e geração integral da transcrição para a interface.
- **`GET /health`**: Verifica a saúde da conexão e se os modelos pesados da IA estão rodando ativamente na inteligência usando o dispositivo configurado (GPU/CPU).

---

## 🤝 Repositórios Oficiais

- **Frontend do Projeto (Interface visual)**: [frontend-agente-estudos-ingles](https://github.com/RenanFerreira0023/frontend-agente-estudos-ingles)
- **Base Inicial de Estudos (Inspiração)**: [chatGenerativo](https://github.com/RenanFerreira0023/chatGenerativo)

Desenvolvido por **[Renan Ferreira](https://github.com/RenanFerreira0023)**. 📄 Licença MIT.
