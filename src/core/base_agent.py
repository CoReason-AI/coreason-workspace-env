from typing import Any

class DeepAgent:
    """
    Base agent class for the DeepAgent framework.
    """
    def __init__(self, **kwargs):
        pass

    def build_standard_deep_agent(self, system_prompt: str, state_schema: Any, tools: list = None, middleware: list = None, subagents: list = None, checkpointer: Any = None, **kwargs):
        """
        Standardizes the compilation of deepagents across the workspace.
        """
        from langchain_openai import ChatOpenAI
        from deepagents.graph import create_deep_agent
        from src.core.config import settings
        
        llm = ChatOpenAI(
            model=settings.LLM_MODEL_NAME,
            api_key=settings.LLM_API_KEY,
            temperature=settings.LLM_TEMPERATURE,
            base_url=settings.LLM_BASE_URL
        )
            
        return create_deep_agent(
            model=llm,
            system_prompt=system_prompt,
            state_schema=state_schema,
            tools=tools or [],
            middleware=middleware or [],
            subagents=subagents or [],
            checkpointer=checkpointer,
            **kwargs
        )
