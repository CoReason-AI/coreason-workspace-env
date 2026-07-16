import os
import yaml
import logging
from typing import Any, Dict
from src.core.base_agent import DeepAgent
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
# Monkeypatch to fix compatibility between langchain-e2b 0.0.5 and deepagents >= 0.6.0
import deepagents.backends.protocol
if not hasattr(deepagents.backends.protocol, "ASYNC_GREP_TIMEOUT"):
    deepagents.backends.protocol.ASYNC_GREP_TIMEOUT = 30.0

from langchain_e2b import E2BDataAnalysisTool
from langgraph.prebuilt import create_react_agent

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
        )
        self.structured_llm = self.llm.with_structured_output(ValidatorOutput)
        
        # Initialize E2B tool
        if settings.E2B_API_KEY:
            self.e2b_tool = E2BDataAnalysisTool(api_key=settings.E2B_API_KEY)
        else:
            self.e2b_tool = None

    def execute(self, payload: dict, session_id: str = None, config: dict = None) -> ValidatorOutput:
        """
        Executes validation checking against standards.
        """
        prompt = self.agent_spec.get("system_prompt", "You are an expert agent validator.")
        
        # Load standards
        standards = "Ensure the output is well formed and deterministic. No mocks or stubs allowed."
        
        logger.info(f"[{session_id}] AgentValidator checking artifacts.")
        
        if config is None:
            # Note: We fallback to empty config if ObservabilityService doesn't exist yet to prevent crash during test
            try:
                from src.core.services.observability_service import ObservabilityService
                obs = ObservabilityService()
                langfuse_cb = obs.get_langfuse_callback(session_id)
                config = {}
                if langfuse_cb:
                    config["callbacks"] = [langfuse_cb]
            except ImportError:
                config = {}
                
        # Setup tools
        tools = []
        if self.e2b_tool:
            tools.append(self.e2b_tool)
            
        # Run ReAct agent to allow code execution before final answer
        if tools:
            react_agent = create_react_agent(self.llm, tools, state_modifier=prompt + f" Standards: {standards}")
            messages = [HumanMessage(content=f"Please validate this output: {payload}")]
            result_state = react_agent.invoke({"messages": messages}, config=config)
            final_message = result_state["messages"][-1]
            
            # Parse the final output into ValidatorOutput
            result = self.structured_llm.invoke([final_message])
        else:
            messages = [
                SystemMessage(content=prompt + f" Standards: {standards}"),
                HumanMessage(content=f"Please validate this output: {payload}")
            ]
            result = self.structured_llm.invoke(messages, config=config)
            
        return result
