import os
import uuid
import yaml
import logging
from typing import Any
from src.core.base_agent import DeepAgent
from deepagents.graph import DeepAgentState

from langchain_core.runnables import RunnableLambda
from deepagents.graph import create_deep_agent

logger = logging.getLogger(__name__)

class AgentPmAgent(DeepAgent):
    """
    Project Manager orchestrating the agent generation pipeline via create_deep_agent.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        yaml_path = os.path.join(os.path.dirname(__file__), "agent.yaml")
        self.agent_spec = {}
        if os.path.exists(yaml_path):
            with open(yaml_path, "r", encoding="utf-8") as f:
                self.agent_spec = yaml.safe_load(f)
                
        base_prompt = self.agent_spec.get("system_prompt", "You are an autonomous PM.")
        pm_prompt = """
You are an autonomous PM.
You have two subagents exposed as tools: prompt_engineer, yaml_compiler.
Step 1: Delegate the user's context to prompt_engineer.
Step 2: Delegate the prompt_engineer's output to yaml_compiler.
Once complete, return the final Markdown response.
"""
        self.system_prompt = f"{base_prompt}\n{pm_prompt}"

    def execute(self, context: Any, session_id: str = None, config: dict = None) -> str:
        """
        Executes pipeline using a ReAct deep agent.
        """
        logger.info(f"[{session_id}] AgentPM initiating ReAct deep agent pipeline.")
        
        from src.agents.prompt_engineer.orchestrator import PromptEngineerAgent
        from src.agents.yaml_compiler.orchestrator import YamlCompilerAgent
        
        from langchain_core.messages import AIMessage
        subagents = [
            {
                "name": "prompt_engineer",
                "description": "Generates a prompt from context.",
                "runnable": RunnableLambda(lambda inputs, config: {"messages": [AIMessage(content=PromptEngineerAgent().execute(inputs, session_id=config.get("configurable", {}).get("thread_id"), config=config))]})
            },
            {
                "name": "yaml_compiler",
                "description": "Compiles a prompt into a yaml definition.",
                "runnable": RunnableLambda(lambda inputs, config: {"messages": [AIMessage(content=YamlCompilerAgent().execute(inputs, session_id=config.get("configurable", {}).get("thread_id"), config=config))]})
            }
        ]

        internal_thread_id = f"{session_id or str(uuid.uuid7())}-pm"
        internal_config = {
            "configurable": {"thread_id": internal_thread_id}
        }
        
        initial_state = {"messages": context} if isinstance(context, list) else {"messages": [("user", str(context))]}
        
        from langgraph.checkpoint.postgres import PostgresSaver
        import psycopg
        from src.core.services.observability_service import ObservabilityService
        obs = ObservabilityService()
        
        with psycopg.connect(obs.pg_dsn) as conn:
            checkpointer = PostgresSaver(conn)
            checkpointer.setup()
            
            graph = self.build_standard_deep_agent(
                system_prompt=self.system_prompt,
                state_schema=DeepAgentState,
                subagents=subagents,
                checkpointer=checkpointer
            )
            
            try:
                result = graph.invoke(initial_state, config=internal_config)
                logger.warning(f"DEBUG: graph.invoke result: {result}")
            except Exception as e:
                logger.error(f"DEBUG: graph.invoke crashed: {e}")
                result = {}
            
        final_message = result.get("messages", [])[-1].content if result.get("messages") else "FAILURE: No output produced."
        return final_message
