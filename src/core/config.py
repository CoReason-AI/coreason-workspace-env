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
    
    # Secrets & Vault (OIDC Federation)
    VAULT_ADDR: str
    VAULT_NAMESPACE: str
    
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
    
    # JWT Security
    JWT_SECRET_KEY: str
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "ignore"

# Instantiate settings. This will immediately throw an error if the .env file
# or environment variables are missing required CISO keys.
settings = Settings()

