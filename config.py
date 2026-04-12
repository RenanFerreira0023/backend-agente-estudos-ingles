from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # App Config
    APP_NAME: str = "DeepSeek-R1 API - Agente de Estudos"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Banco de Dados Config
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "1234"
    DB_NAME: str = "super-aluno-ingles"

# Agora incluído na classe Settings:
    USE_GPU: bool = True
    DEVICE: str = "gpu" if USE_GPU else "cpu"


    
    # Model Config
    MODEL_NAME: str = "DeepSeek-R1-Distill-Llama-8B-Q4_0.gguf"
    MODEL_PATH: str = "./models"
    WHISPER_MODEL_NAME: str = "base" # Pode ser tiny, base, small, medium, large
    
    # Security Config
    ALLOWED_ORIGINS: List[str] = ["*"]
    TRUSTED_HOSTS: List[str] = ["*"]
    
    # Generative Config
    CONTEXT_SIZE: int = 16384
    MAX_TOKENS: int = 2048
    TEMPERATURE: float = 0.6

    class Config:
        env_file = ".env"

settings = Settings()
