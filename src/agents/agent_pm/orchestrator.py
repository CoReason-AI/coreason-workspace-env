import os
import yaml
import logging
from typing import Any, Dict, TypedDict
from src.core.base_agent import DeepAgent
from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)

from src.core.ontology import MakerCheckerState

class AgentPmAgent(DeepAgent):
    """
    Project Manager for orchestrating the Maker-Checker pipeline.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        yaml_path = os.path.join(os.path.dirname(__file__), "agent.yaml")
        if os.path.exists(yaml_path):
            with open(yaml_path, "r", encoding="utf-8") as f:
                self.agent_spec = yaml.safe_load(f)
                
        graph = StateGraph(MakerCheckerState)
        graph.add_node("maker", self._run_maker)
        graph.add_node("validator", self._run_validator)
        
        graph.set_entry_point("maker")
        graph.add_edge("maker", "validator")
        graph.add_conditional_edges(
            "validator",
            self._route_validation,
            {
                "success": END,
                "retry": "maker",
                "failed": END
            }
        )
        self.graph_builder = graph
        self.graph = self.graph_builder.compile()
        
    from langchain_core.runnables import RunnableConfig
        
    def _run_maker(self, state: MakerCheckerState, config: RunnableConfig):
        from src.agents.prompt_engineer.orchestrator import PromptEngineerAgent
        from src.agents.yaml_compiler.orchestrator import YamlCompilerAgent
        
        session_id = config.get("configurable", {}).get("thread_id")
        prompt_worker = PromptEngineerAgent()
        yaml_worker = YamlCompilerAgent()
        
        context = state.get("messages", [])
        feedback = state.get("feedback", "")
        worker_context = f"{context}\nFeedback from previous run: {feedback}" if feedback else str(context)
        
        attempts = state.get("attempts", 0) + 1
        
        # 1. Generate Prompt
        prompt_result = prompt_worker.execute(worker_context, session_id=session_id, config=config)
        
        # 2. Pass to YAML Compiler
        compiler_context = f"{worker_context}\nPrompt Output:\n{prompt_result}"
        final_result = yaml_worker.execute(compiler_context, session_id=session_id, config=config)
        
        return {"worker_result": str(final_result), "attempts": attempts}

    def _run_validator(self, state: MakerCheckerState, config: RunnableConfig):
        from src.agents.agent_validator.orchestrator import AgentValidatorAgent
        validator = AgentValidatorAgent()
        session_id = config.get("configurable", {}).get("thread_id")
        
        validation = validator.execute(state["worker_result"], session_id=session_id, config=config)
        if validation.is_valid:
            return {"feedback": "", "final_output": f"SUCCESS: {state['worker_result']}"}
        else:
            return {"feedback": validation.feedback, "final_output": "FAILURE"}
            
    def _route_validation(self, state: MakerCheckerState):
        if state.get("final_output", "").startswith("SUCCESS"):
            return "success"
        elif state.get("attempts", 0) >= 3:
            return "failed"
        else:
            return "retry"

    def execute(self, state: dict, session_id: str = None, config: dict = None) -> str:
        """
        Executes Maker-Checker loop using a declarative LangGraph StateGraph.
        """
        import uuid
        
        logger.info(f"[{session_id}] AgentPM initiating LangGraph StateGraph pipeline.")
        initial_state = {
            "messages": state.get("messages", []),
            "worker_result": "",
            "feedback": "",
            "attempts": 0,
            "final_output": ""
        }
        
        from langgraph.checkpoint.postgres import PostgresSaver
        import psycopg
        from src.core.services.observability_service import ObservabilityService
        obs = ObservabilityService()
        
        with psycopg.connect(obs.pg_dsn) as conn:
            checkpointer = PostgresSaver(conn)
            checkpointer.setup()
            graph_with_checkpointer = self.graph_builder.compile(checkpointer=checkpointer)
            
            if config is None:
                langfuse_cb = obs.get_langfuse_callback(session_id)
                config = {
                    "configurable": {"thread_id": session_id or str(uuid.uuid7())}
                }
                if langfuse_cb:
                    config["callbacks"] = [langfuse_cb]
                
            result = graph_with_checkpointer.invoke(initial_state, config=config)
        
        if result.get("final_output", "").startswith("SUCCESS"):
            return result["final_output"]
        return "FAILURE: Max retries exceeded during validation loop."
