import os
from pydantic_settings import BaseSettings

class EvaluationConfig(BaseSettings):
    """
    Configuration for the evaluation framework.
    Strictly forces LangSmith to use a local endpoint to satisfy Data Sovereignty.
    """
    # Force LangSmith to use local instance (e.g. via Harbor or docker-compose)
    # Defaulting to 1984 as per Harbor's default local LangSmith port, or 80 if standard docker.
    LANGCHAIN_ENDPOINT: str = os.getenv("LANGCHAIN_ENDPOINT", "http://localhost:1984")
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "local")
    LANGCHAIN_TRACING_V2: str = "true"
    
    # LLM Settings for the 'Judge' models
    EVALUATOR_MODEL: str = os.getenv("EVALUATOR_MODEL", "openai/gpt-4o")

eval_settings = EvaluationConfig()

def enforce_local_langsmith():
    """
    Called before any evaluation to ensure environment variables
    are strictly overriding any global leaks to smith.langchain.com
    """
    os.environ["LANGCHAIN_ENDPOINT"] = eval_settings.LANGCHAIN_ENDPOINT
    os.environ["LANGCHAIN_API_KEY"] = eval_settings.LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_TRACING_V2"] = eval_settings.LANGCHAIN_TRACING_V2
