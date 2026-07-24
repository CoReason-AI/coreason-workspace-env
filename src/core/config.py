import os
from pydantic_settings import BaseSettings, SettingsConfigDict

# Ensure Langfuse is disabled locally by default unless explicitly configured in .env
os.environ.setdefault("LANGFUSE_PUBLIC_KEY", "")
os.environ.setdefault("LANGFUSE_SECRET_KEY", "") 
class Settings(BaseSettings):
    """
    Strict SSOT Configuration for the Platform.
    """
    # Core
    ENVIRONMENT: str = "development"
    
    # LLM Configuration
    LLM_MODEL_NAME: str = "nvidia/nemotron-3-nano-30b-a3b:free"
    LLM_API_KEY: str = "LLM_API_KEY"
    LLM_TEMPERATURE: float = 0.0
    EMBEDDING_MODEL_NAME: str = "local-embedding-v1"
    EMBEDDING_BASE_URL: str = "http://localhost:11434/v1"
    
    LLM_BASE_URL: str = "https://openrouter.ai/api/v1"
    
    # E2B Sandbox
    E2B_API_KEY: str = ""
    
    # Dify Configuration
    DIFY_API_URL: str = "http://localhost:5001/v1"
    DIFY_API_KEY: str = ""

    # Checkpointer Database (Postgres)
    POSTGRES_USER: str = "coreason_admin"
    POSTGRES_PASSWORD: str = "secure_dev_password"
    POSTGRES_DB: str = "langgraph_state"
    POSTGRES_HOST: str = "postgres_checkpointer"
    POSTGRES_PORT: int = 5432

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra="ignore")
 
settings = Settings()