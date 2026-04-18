from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    HUGGINGFACE_API_KEY: Optional[str] = None
    LANGSMITH_API_KEY: Optional[str] = None

    # Model Settings
    DEFAULT_MODEL: str = "gpt-4o"
    DEFAULT_TEMPERATURE: float = 0.7

    # Ollama Settings
    OLLAMA_BASE_URL: Optional[str] = "http://localhost:11434"
    OLLAMA_MODEL: Optional[str] = "llama3"

    # Application Settings
    APP_NAME: str = "LangChain LLM Toolkit"
    DEBUG: bool = False

    # RAG Settings
    VECTOR_STORE_TYPE: str = "qdrant"
    RAG_QDRANT_PATH: str = "./qdrant_storage"
    RAG_FAISS_PATH: str = "./vector_store"
    RAG_COLLECTION_NAME: str = "langchain_documents"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()
