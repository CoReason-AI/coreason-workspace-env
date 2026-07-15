import os
import yaml
import logging
from deepagents import DeepAgent

logger = logging.getLogger(__name__)

class CausalInferenceConsultantAgent(DeepAgent):
    """
    Deterministic LangGraph execution node for the causal_inference_consultant.
    Executes formal Neurosymbolic reasoning utilizing PyWhy via MCP tool boundaries.
    """
    def __init__(self, **kwargs):
        yaml_path = os.path.join(os.path.dirname(__file__), "agent.yaml")
        with open(yaml_path, "r", encoding="utf-8") as f:
            self.agent_spec = yaml.safe_load(f)
            
        super().__init__(**kwargs)
        logger.info(f"Initialized {self.agent_spec.get('name')}")
