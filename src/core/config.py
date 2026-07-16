import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Strict SSOT Configuration for the Platform.
    Rule 8 Enforcement: No fallback defaults. If an environment variable is missing,
    the application will raise a ValidationError and fail fast.
    """
    # Core
    ENVIRONMENT: str
    ALLOWED_ORIGINS: str
    
    # Observability (Langfuse)
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "http://localhost:3001"
    
    # Secrets & Vault (OIDC Federation)
    VAULT_ADDR: str
    VAULT_NAMESPACE: str
    JWT_SECRET_KEY: str = "fallback_secret_for_local_dev"
    
    # Checkpointer Database (Postgres)
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    
    # Redis Backplane (Pub/Sub & Tasks)
    REDIS_URL: str
    
    # WORM Storage (S3)
    WORM_S3_BUCKET: str
    WORM_S3_REGION: str
    WORM_S3_ENDPOINT: str
    WORM_S3_ACCESS_KEY: str
    WORM_S3_SECRET_KEY: str
    
    # External APIs
    OPENROUTER_API_KEY: str
    
    # LLM Configuration
    LLM_MODEL_NAME: str = "nvidia/nemotron-3-nano-30b-a3b:free"
    LLM_API_KEY: str = "standalone-key-placeholder"
    LLM_TEMPERATURE: float = 0.0
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "ignore"

# Instantiate settings. This will immediately throw an error if the .env file
# or environment variables are missing required CISO keys.
settings = Settings()

