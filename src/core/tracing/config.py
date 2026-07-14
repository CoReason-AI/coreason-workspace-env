"""
Langfuse configuration — reads from environment variables.
"""
import os
from typing import Optional


class LangfuseConfig:
    """Configuration for the Langfuse tracing integration."""

    def __init__(self):
        self.host: str = os.getenv("LANGFUSE_HOST", "http://localhost:3000")
        self.public_key: str = os.getenv("LANGFUSE_PUBLIC_KEY", "pk-lf-coreason-dev")
        self.secret_key: str = os.getenv("LANGFUSE_SECRET_KEY", "sk-lf-coreason-dev")
        self.enabled: bool = os.getenv("LANGFUSE_ENABLED", "true").lower() == "true"

    @property
    def is_configured(self) -> bool:
        """Check if Langfuse is properly configured."""
        return bool(self.host and self.public_key and self.secret_key)


# Singleton
langfuse_config = LangfuseConfig()
