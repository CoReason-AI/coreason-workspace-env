import os
import yaml
import logging
from typing import Any
from src.core.base_agent import DeepAgent
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class PromptOutput(BaseModel):
    system_prompt: str = Field(description="The generated system prompt.")
    few_shot_examples: list[str] = Field(description="Examples to guide the LLM.")

class PromptEngineerAgent(DeepAgent):
    """
    Deterministic worker for Prompt engineering.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        yaml_path = os.path.join(os.path.dirname(__file__), "agent.yaml")
        if os.path.exists(yaml_path):
            with open(yaml_path, "r", encoding="utf-8") as f:
                self.agent_spec = yaml.safe_load(f)
        
        from src.core.config import settings
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL_NAME,
            api_key=settings.LLM_API_KEY,
            temperature=settings.LLM_TEMPERATURE,
            base_url=settings.LLM_BASE_URL
        ).with_structured_output(PromptOutput)

    def execute(self, context: dict, session_id: str = None) -> dict:
        """
        Executes deterministically based on saturated context.
        """
        prompt = self.agent_spec.get("system_prompt", "You are an expert prompt engineer.")
        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=f"Requirements: {context}")
        ]
        
        logger.info(f"[{session_id}] PromptEngineer executing deterministic generation.")
        result = self.llm.invoke(messages)
        return {"prompt_output": result.dict()}
