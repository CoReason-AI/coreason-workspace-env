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
        Executes pipeline using a deterministic linear StateGraph.
        """
        logger.info(f"*** [{session_id}] AgentPM initiating deterministic StateGraph pipeline! ***")
        
        from src.agents.prompt_engineer.orchestrator import PromptEngineerAgent
        from src.agents.yaml_compiler.orchestrator import YamlCompilerAgent
        from langgraph.graph import StateGraph, START, END
        from langchain_core.messages import AIMessage
        
        # 1. Prepare initial state
        initial_state = {"messages": context} if isinstance(context, list) else {"messages": [("user", str(context))]}
        
        # 2. Define node execution logic
        def run_prompt_engineer(state: DeepAgentState) -> dict:
            logger.info(f"[{session_id}] PM Step 1: Delegating to PromptEngineerAgent")
            messages = state.get("messages", [])
            last_msg = messages[-1].content if messages else str(state)
            pe_output = PromptEngineerAgent().execute(last_msg, session_id=session_id, config=config)
            return {"messages": [AIMessage(content=pe_output)]}
            
        def run_yaml_compiler(state: DeepAgentState) -> dict:
            logger.info(f"[{session_id}] PM Step 2: Delegating to YamlCompilerAgent")
            messages = state.get("messages", [])
            last_msg = messages[-1].content if messages else ""
            yc_output = YamlCompilerAgent().execute(last_msg, session_id=session_id, config=config)
            return {"messages": [AIMessage(content=yc_output)]}
            
        # 3. Build linear StateGraph
        builder = StateGraph(DeepAgentState)
        builder.add_node("prompt_engineer", run_prompt_engineer)
        builder.add_node("yaml_compiler", run_yaml_compiler)
        
        builder.add_edge(START, "prompt_engineer")
        builder.add_edge("prompt_engineer", "yaml_compiler")
        builder.add_edge("yaml_compiler", END)
        
        graph = builder.compile()
        
        # 4. Invoke graph execution
        try:
            result = graph.invoke(initial_state, config=config or {})
            logger.info(f"[{session_id}] PM deterministic pipeline executed successfully.")
        except Exception as e:
            logger.error(f"[{session_id}] PM deterministic pipeline failed: {e}")
            result = {}
            
        final_message = result.get("messages", [])[-1].content if result.get("messages") else "FAILURE: No output produced."
        return final_message
