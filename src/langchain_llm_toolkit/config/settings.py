from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API Keys
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None
    HUGGINGFACE_API_KEY: str | None = None
    LANGSMITH_API_KEY: str | None = None

    # OpenAI-compatible API Base URL (e.g. Agnes, DeepSeek)
    OPENAI_API_BASE: str | None = None

    # Model Settings
    DEFAULT_MODEL: str = "deepseek-chat"
    DEFAULT_TEMPERATURE: float = 0.7

    # Ollama Settings
    OLLAMA_BASE_URL: str | None = "http://localhost:11434"
    OLLAMA_MODEL: str | None = "llama3"

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
