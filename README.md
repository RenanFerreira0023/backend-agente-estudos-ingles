# ✦ Backend - Agente de Estudos de Inglês

Este projeto é o back-end para um agente inteligente de estudos de inglês. Ele fornece uma API robusta utilizando **DeepSeek-R1** (via GPT4All) para processamento de linguagem natural e **Whisper** para transcrição de áudio e vídeo, permitindo uma experiência completa de aprendizado.

---

## 🚀 Funcionalidades

-   **Chat Inteligente**: Interação fluida com o modelo DeepSeek-R1-Distill-Llama-8B.
-   **Suporte a Arquivos**: Capacidade de processar conteúdo de arquivos enviados (via Base64) junto com o prompt.
-   **Transcrição de Vídeo**: Endpoint para receber vídeos, extrair áudio e transcrever o conteúdo utilizando Whisper.
-   **Aceleração de Hardware**: Suporte nativo para GPU (CUDA) tanto para o LLM quanto para a transcrição.
-   **Streaming de Respostas**: Respostas em tempo real para o chat, melhorando a experiência do usuário.

---

## 🛠️ Tecnologias Utilizadas

-   **[FastAPI](https://fastapi.tiangolo.com/)**: Framework web de alta performance.
-   **[GPT4All](https://gpt4all.io/)**: Biblioteca para execução local de LLMs.
-   **[OpenAI Whisper](https://github.com/openai/whisper)**: Sistema de reconhecimento de fala (ASR) robusto.
-   **[Pydantic](https://docs.pydantic.dev/)**: Validação de dados e configurações.
-   **[Uvicorn](https://www.uvicorn.org/)**: Servidor ASGI para produção e desenvolvimento.

---

## ⚙️ Instalação e Execução

### 1. Clonar o Repositório
```bash
git clone https://github.com/RenanFerreira0023/backend-agente-estudos-ingles.git
cd backend-agente-estudos-ingles
```

### 2. Configurar o Ambiente Virtual
```bash
python -m venv venv
venv\Scripts\activate  # No Windows
source venv/bin/activate  # No Linux/Mac
```

### 3. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 4. Executar a API
```bash
python api.py
```
O servidor estará disponível em `http://localhost:8000`.

---

## 🛣️ Rotas da API

### `POST /chat`
Envia um prompt para o modelo. Suporta envio de arquivo opcional em Base64.
- **Payload**:
  ```json
  {
    "prompt": "Como digo 'maçã' em inglês?",
    "file": "base64_encoded_content_optional"
  }
  ```
- **Resposta**: Streaming de texto (Plain Text).

### `POST /uploadVideo`
Recebe um vídeo em Base64, salva temporariamente e retorna a transcrição.
- **Payload**:
  ```json
  {
    "video_base64": "...",
    "filename": "aula_ingles.mp4"
  }
  ```
- **Resposta**: `{"text": "Transcrição do vídeo aqui..."}`

### `GET /health`
Verifica o status da API e do modelo carregado.

---

## 💻 Configuração de Hardware

O projeto permite alternar entre CPU e GPU através do arquivo `config.py`:

- **GPU (Recomendado)**: Defina `USE_GPU = True`. Requer drivers NVIDIA atualizados e o **NVIDIA CUDA Toolkit** instalado. 
- **CPU**: Defina `USE_GPU = False`. Útil para sistemas sem placa de vídeo dedicada ou com problemas de memória (VRAM).

*Nota: Se a inicialização na GPU falhar, o sistema tentará automaticamente um fallback para a CPU.*

---

## 🤝 Créditos

Este projeto foi inspirado e utiliza conceitos do repositório:
👉 **[chatGenerativo](https://github.com/RenanFerreira0023/chatGenerativo)**

Desenvolvido por [Renan Ferreira](https://github.com/RenanFerreira0023).

---

## 📄 Licença
Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
