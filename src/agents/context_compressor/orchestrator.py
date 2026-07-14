import os
import yaml
import logging
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

class ContextCompressorAgent:
    """
    Native DeepAgent Harness for the Context Compressor Sub-Agent.
    """
    def __init__(self, model_override: str = None):
        yaml_path = os.path.join(os.path.dirname(__file__), "agent.yaml")
        with open(yaml_path, "r", encoding="utf-8") as f:
            self.agent_spec = yaml.safe_load(f)
            
        self.llm = ChatOpenAI(
            model=model_override or "nvidia/nemotron-3-nano-30b-a3b:free",
            api_key="sovereign-key-placeholder",
            temperature=0.1 # Very low temperature for strict factual extraction
        )
        
        self.tools = []
        logger.info(f"Initialized {self.agent_spec.get('name')}")

    def execute(self, raw_payload: str, compression_goal: str, session_id: str) -> str:
        """
        Executes the DeepAgent compression.
        """
        try:
            from deepagents import create_deep_agent
            
            graph = create_deep_agent(
                model=self.llm,
                tools=self.tools,
                system_prompt=self.agent_spec.get("system_prompt")
            )
            
            config = {"configurable": {"thread_id": session_id}}
            result = graph.invoke(
                {"messages": [("user", f"Goal: {compression_goal}\n\nPayload:\n{raw_payload}")]},
                config=config
            )
            return result['messages'][-1].content
        except ImportError:
            logger.warning("deepagents package missing, acting as mock execution.")
            return f"[COMPRESSED DATA for '{compression_goal}']: ... (High signal data extracted) ..."
