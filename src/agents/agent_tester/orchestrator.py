import os
import yaml
from typing import Any
from src.core.base_agent import DeepAgent
from deepagents.graph import DeepAgentState

class AgentTesterAgent(DeepAgent):
    """
    Agent Tester Agent for generating test suites and acceptance criteria.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        yaml_path = os.path.join(os.path.dirname(__file__), "agent.yaml")
        self.agent_spec = {}
        if os.path.exists(yaml_path):
            with open(yaml_path, "r", encoding="utf-8") as f:
                self.agent_spec = yaml.safe_load(f)

        self.system_prompt = self.agent_spec.get("system_prompt", "You are the QA tester agent.")

    async def execute(self, context: dict, session_id: str = None, config: dict = None) -> Any:
        prompt = self.system_prompt
        
        # We use the standard DeepAgent factory wrapper which handles LangGraph creation
        # We must inject the StateBackend to provide the virtual filesystem tools so it can write tests
        from deepagents.acp.backends.local import StateBackend
        backend = StateBackend()
        
        graph = self.build_standard_deep_agent(
            system_prompt=prompt,
            state_schema=DeepAgentState,
            tools=backend.get_tools()
        )
        
        if config is None:
            config = {"configurable": {"thread_id": session_id or "default_tester"}}
            
        return await graph.ainvoke(context, config=config)
