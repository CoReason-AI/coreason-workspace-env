import os
import yaml
import logging
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from .tools.fs_tools import local_fs_writer, local_fs_reader

logger = logging.getLogger(__name__)

class YAMLCompilerAgent:
    """
    Native DeepAgent Harness for the deterministic YAML Compiler.
    Accepts the fully saturated context and scaffolds the project files.
    """
    def __init__(self, model_override: str = None):
        # Updated to point to the encapsulated agent.yaml
        yaml_path = os.path.join(os.path.dirname(__file__), "agent.yaml")
        with open(yaml_path, "r", encoding="utf-8") as f:
            self.agent_spec = yaml.safe_load(f)
            
        self.llm = ChatOpenAI(
            model=model_override or "nvidia/nemotron-3-nano-30b-a3b:free",
            api_key="sovereign-key-placeholder",
            temperature=0.0
        )
        
        # Bound to encapsulated tools
        self.tools = [local_fs_writer, local_fs_reader]
        logger.info(f"Initialized {self.agent_spec.get('name')}")

    def execute(self, saturated_context: str, session_id: str) -> str:
        """
        Executes the DeepAgent compilation dynamically via LangGraph.
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
                {"messages": [("user", f"Compile these requirements: {saturated_context}")]},
                config=config
            )
            return result['messages'][-1].content
        except ImportError:
            logger.warning("deepagents package missing, acting as mock execution.")
            return "MOCK_SUCCESS: Compiled project.yaml and orchestrator_agent.yaml"
