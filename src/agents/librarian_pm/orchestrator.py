import os
import yaml
import logging
from typing import Any, Dict, TypedDict
from src.core.base_agent import DeepAgent
from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    messages: list
    worker_result: str
    feedback: str
    attempts: int
    final_output: str

class LibrarianPmAgent(DeepAgent):
    """
    Project Manager for orchestrating the Knowledge Base pipeline.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        yaml_path = os.path.join(os.path.dirname(__file__), "agent.yaml")
        if os.path.exists(yaml_path):
            with open(yaml_path, "r", encoding="utf-8") as f:
                self.agent_spec = yaml.safe_load(f)
                
        graph = StateGraph(AgentState)
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
        self.graph = graph.compile()
        
    def _run_maker(self, state: AgentState):
        from src.agents.context_compressor.orchestrator import ContextCompressorAgent
        worker = ContextCompressorAgent()
        context = state.get("messages", [])
        feedback = state.get("feedback", "")
        worker_context = f"{context}\nFeedback from previous run: {feedback}" if feedback else str(context)
        
        attempts = state.get("attempts", 0) + 1
        result = worker.execute(worker_context, "librarian_pm_loop")
        return {"worker_result": result, "attempts": attempts}

    def _run_validator(self, state: AgentState):
        from src.agents.agent_validator.orchestrator import AgentValidatorAgent
        validator = AgentValidatorAgent()
        
        validation = validator.execute(state["worker_result"], "librarian_pm_loop")
        if validation.is_valid:
            return {"feedback": "", "final_output": f"SUCCESS: {state['worker_result']}"}
        else:
            return {"feedback": validation.feedback, "final_output": "FAILURE"}
            
    def _route_validation(self, state: AgentState):
        if state.get("final_output", "").startswith("SUCCESS"):
            return "success"
        elif state.get("attempts", 0) >= 3:
            return "failed"
        else:
            return "retry"

    def execute(self, state: dict, session_id: str = None) -> str:
        """
        Executes Maker-Checker loop using a declarative LangGraph StateGraph.
        """
        logger.info(f"[{session_id}] LibrarianPM initiating LangGraph StateGraph pipeline.")
        initial_state = {
            "messages": state.get("messages", []),
            "worker_result": "",
            "feedback": "",
            "attempts": 0,
            "final_output": ""
        }
        
        result = self.graph.invoke(initial_state)
        
        if result.get("final_output", "").startswith("SUCCESS"):
            return result["final_output"]
        return "FAILURE: Max retries exceeded during validation loop."
