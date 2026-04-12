# 🎓 Backend - Agente de Estudos de Inglês ("Super Aluno")

Este é um projeto de **LLM (Large Language Model)** que implementa um **Agente de IA especializado** no suporte ao aprendizado de inglês. Diferente de um chat comum, este agente foi "treinado" (via engenharia de prompt avançada e ferramentas externas) para atuar como um **"Super Aluno"**.

### 🧠 O que o Agente faz?
O coração do projeto é um agente inteligente que:
- **Analisa Transcrições:** Processa diálogos de aulas particulares para extrair o que é mais importante.
- **Identifica Anotações:** Detecta automaticamente quando um professor pede para o aluno anotar um vocabulário ou frase.
- **Dicas de Pronúncia:** Fornece guias fonéticos e dicas para palavras difíceis identificadas na aula.
- **Autonomia com Ferramentas:** Utiliza ferramentas como busca em dicionários e salvamento de flashcards de forma autônoma (ReAct pattern).
- **Interação Natural:** Responde sempre em Português (PT-BR), mantendo uma didática de um colega de estudos dedicado.

Construído com **FastAPI**, o sistema utiliza o modelo **DeepSeek-R1** e transcreve vídeoaulas localmente com o **OpenAI Whisper**.


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

> [!TIP]
> **Acesso Externo / Como liberar no Windows Firewall:**
> Se precisar que a API seja acessível por outros dispositivos, siga este passo a passo:
> 1. Pressione a tecla `Win` e procure por **"Windows Defender Firewall com Segurança Avançada"**.
> 2. No menu à esquerda, clique em **Regras de Entrada**.
> 3. No menu à direita, clique em **Nova Regra...**.
> 4. Escolha o tipo **Porta** e clique em Avançar.
> 5. Selecione **TCP** e em Portas locais específicas, digite **8000**.
> 6. Selecione **Permitir a conexão** e avance até o final.
> 7. Dê um nome como `Backend Super Aluno (8000)` e finalize.

---

## 🛠️ Resumo Técnico das Features Adicionadas

- **Ajustes de Persona Externalizados (`prompts.py`):** Todo o comportamento da IA como "Super Aluno" que fala PT-BR e captura anotações e pronúncias de aulas foi isolado em um módulo prático.
- **Auto-Correção (Agent Loop ReAct):** O servidor percebe e contorna falhas na geração das requisições JSON da IA de forma transparente ao usuário (trabalhando limites de tentativas).
- **Adequação Limite de Token:** O sistema adota limites agressivos de Tokens (16K ctx) garantindo que os vídeos passem no *input*.
- **Rotas Principais:** Trabalhos por trás dos panos nos endpoints `/chat` (gerado em pedaços e validado) e fluxo rápido de áudio no `/uploadVideo` acelerado via CUDA 12.

---
**Desenvolvido por [Renan Ferreira](https://github.com/RenanFerreira0023)**.  
Acesse a Interface: [frontend-agente-estudos-ingles](https://github.com/RenanFerreira0023/frontend-agente-estudos-ingles)
