"""
LangSmith configuration — reads from environment variables.
"""
import os


class LangSmithConfig:
    """Configuration for the LangSmith tracing integration."""

    def __init__(self):
        self.endpoint: str = os.getenv("LANGCHAIN_ENDPOINT", "http://localhost:1984")
        self.api_key: str = os.getenv("LANGCHAIN_API_KEY", "local")
        self.tracing_v2: str = os.getenv("LANGCHAIN_TRACING_V2", "true")
        self.project: str = os.getenv("LANGCHAIN_PROJECT", "coreason-dev")

    @property
    def is_configured(self) -> bool:
        """Check if LangSmith is properly configured."""
        return bool(self.endpoint and self.api_key)


# Singleton
langsmith_config = LangSmithConfig()
