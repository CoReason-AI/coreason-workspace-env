import os
import yaml
import logging
from typing import Any, Dict
from src.core.base_agent import DeepAgent
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class ValidatorOutput(BaseModel):
    is_valid: bool = Field(description="True if the output conforms to standards, False otherwise.")
    feedback: str = Field(description="Actionable feedback for remediation if invalid.")

class AgentValidatorAgent(DeepAgent):
    """
    Checker logic for evaluating generated artifacts.
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
        ).with_structured_output(ValidatorOutput)

    def execute(self, payload: dict, session_id: str = None, config: dict = None) -> ValidatorOutput:
        """
        Executes validation checking against standards.
        """
        prompt = self.agent_spec.get("system_prompt", "You are an expert agent validator.")
        
        # Load standards
        standards = "Ensure the output is well formed and deterministic. No mocks or stubs allowed."
        
        messages = [
            SystemMessage(content=prompt + f" Standards: {standards}"),
            HumanMessage(content=f"Please validate this output: {payload}")
        ]
        
        logger.info(f"[{session_id}] AgentValidator checking artifacts.")
        
        if config is None:
            from src.core.services.observability_service import ObservabilityService
            obs = ObservabilityService()
            langfuse_cb = obs.get_langfuse_callback(session_id)
            config = {}
            if langfuse_cb:
                config["callbacks"] = [langfuse_cb]
            
        result = self.llm.invoke(messages, config=config)
        return result
