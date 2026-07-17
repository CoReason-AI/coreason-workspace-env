import os
import yaml
import logging
from typing import Any
from src.core.base_agent import DeepAgent
from langchain_core.messages import HumanMessage
from deepagents.graph import DeepAgentState

logger = logging.getLogger(__name__)

class YamlCompilerAgent(DeepAgent):
    """
    Deterministic worker for YAML compilation via DeepAgent.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        yaml_path = os.path.join(os.path.dirname(__file__), "agent.yaml")
        self.agent_spec = {}
        if os.path.exists(yaml_path):
            with open(yaml_path, "r", encoding="utf-8") as f:
                self.agent_spec = yaml.safe_load(f)
        
        base_prompt = self.agent_spec.get("system_prompt", "You are an expert YAML compiler.")
        self.system_prompt = f"{base_prompt}\nYOU MUST output your final result as a Markdown block (e.g. ```yaml ... ```)."

    def execute(self, context: Any, session_id: str = None, config: dict = None) -> str:
        """
        Executes deterministic generation via DeepAgent loop.
        """
        logger.info(f"[{session_id}] YamlCompiler executing via DeepAgent.")
        
        graph = self.build_standard_deep_agent(
            system_prompt=self.system_prompt,
            state_schema=DeepAgentState,
        )
        
        initial_state = {"messages": [HumanMessage(content=f"Requirements: {context}")]}
        result = graph.invoke(initial_state, config=config or {})
        
        final_message = result.get("messages", [])[-1].content if result.get("messages") else "FAILURE: No output produced."
        return final_message
