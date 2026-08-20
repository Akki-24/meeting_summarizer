import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Meeting Summarizer API"
    API_V1_STR: str = "/api/v1"
    UPLOAD_DIR: str = os.path.abspath("./uploads")
    
    # DB
    DATABASE_URL: str = "sqlite:///./meetings.db"
    CHROMA_PERSIST_DIR: str = os.path.abspath("./chroma_db")
    
    # LLM Settings
    LLM_PROVIDER: str = "gemini"  # "gemini" or "ollama"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.6-flash"
    
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"
    
    # ASR Settings
    WHISPER_MODEL_SIZE: str = "base"
    WHISPER_DEVICE: str = "cpu"  # "cpu" or "cuda"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)