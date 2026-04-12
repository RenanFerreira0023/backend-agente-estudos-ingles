# 🎓 Backend - Agente de Estudos de Inglês ("Super Aluno")

Este é o backend de um agente inteligente desenhado para atuar como um **"Super Aluno"** no estudo de inglês. 
Ele analisa transcrições de aulas particulares, identifica palavras que o professor pediu para anotar, resume vocabulários e dá dicas de pronúncia — interagindo sempre em **Português do Brasil (PT-BR)**.

Construído com **FastAPI**, o sistema roda o modelo de inteligência artificial **DeepSeek-R1** e transcreve as vídeoaulas localmente usando o **OpenAI Whisper**. O agente possui histórico persistente (PostgreSQL) e consegue utilizar ferramentas (dicionário e flashcards) de forma autônoma.

---

## ⚠️ Requisitos Fundamentais (Hardware e Software)

Para que o projeto funcione usando aceleração de vídeo (GPU) sem problemas, você DEVE possuir:
- **[Python 3.12](https://www.python.org/downloads/release/python-3128/)**
- **[CUDA Toolkit 12](https://developer.nvidia.com/cuda-downloads)**
- Placa de Vídeo NVIDIA Compatível (ex: linha RTX 40xx). *(Pode ser rodado no processador definindo `USE_GPU=False`, porém será mais lento).*
- Banco de dados **[PostgreSQL](https://www.postgresql.org/download/)**.

> [!IMPORTANT]
> **Por que não usar a última versão?**
> - **Python 3.12:** Versões mais recentes (como a 3.13) podem ainda não possuir bibliotecas pré-compiladas (wheels) para dependências críticas como o PyTorch e Whisper em todos os ambientes, o que pode causar falhas na instalação.
> - **CUDA 12:** O motor de inferência local e as bibliotecas de transcrição foram validados especificamente para esta versão do Toolkit. Usar versões anteriores ou muito experimentais pode resultar em erros de carregamento de DLLs (`LoadLibraryExW`).

---

## ⚙️ Instalação e Execução Limpa

1. Clone e configure o ambiente (Lembrando: Python 3.12+):
```bash
git clone https://github.com/RenanFerreira0023/backend-agente-estudos-ingles.git
cd backend-agente-estudos-ingles
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

2. Configure seu arquivo de variáveis de ambiente (`.env`) na raiz:
```env
# Banco de Dados
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=sua-senha      # <- Altere aqui
DB_NAME=super-aluno-ingles # <- O banco já deve existir

# Configurações do Motor de IA
USE_GPU=True
MODEL_NAME=DeepSeek-R1-Distill-Llama-8B-Q4_0.gguf
CONTEXT_SIZE=16384         # Contexto expandido para digerir aulas densas
```

3. Inicie o Servidor:
```bash
python api.py
```
A API rodará localmente respondendo na porta `8000`.

---

## 🛠️ Resumo Técnico das Features Adicionadas

- **Ajustes de Persona Externalizados (`prompts.py`):** Todo o comportamento da IA como "Super Aluno" que fala PT-BR e captura anotações e pronúncias de aulas foi isolado em um módulo prático.
- **Auto-Correção (Agent Loop ReAct):** O servidor percebe e contorna falhas na geração das requisições JSON da IA de forma transparente ao usuário (trabalhando limites de tentativas).
- **Adequação Limite de Token:** O sistema adota limites agressivos de Tokens (16K ctx) garantindo que os vídeos passem no *input*.
- **Rotas Principais:** Trabalhos por trás dos panos nos endpoints `/chat` (gerado em pedaços e validado) e fluxo rápido de áudio no `/uploadVideo` acelerado via CUDA 12.

---
**Desenvolvido por [Renan Ferreira](https://github.com/RenanFerreira0023)**.  
Acesse a Interface: [frontend-agente-estudos-ingles](https://github.com/RenanFerreira0023/frontend-agente-estudos-ingles)
