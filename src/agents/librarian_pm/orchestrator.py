import os
import yaml
import logging
import zipfile
import glob
from typing import Any, Dict, TypedDict
from src.core.base_agent import DeepAgent
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

from src.core.ontology import MakerCheckerState
from pydantic import BaseModel, Field

class PathExtraction(BaseModel):
    has_path: bool = Field(description="True if a file or directory path was mentioned in the context.")
    extracted_path: str = Field(description="The extracted path string, or empty if none.")

def extract_and_read_context(path: str) -> str:
    """Extracts zip files and reads all text/code files in the given directory path to provide the codebase context."""
    extracted_path = os.path.abspath(path.strip('\'"'))
    if not os.path.exists(extracted_path):
        return f"Path does not exist: {extracted_path}"
    
    # Extract nested zips
    nested_zips = glob.glob(os.path.join(extracted_path, '**', '*.zip'), recursive=True)
    for zpath in nested_zips:
        try:
            with zipfile.ZipFile(zpath, 'r') as zref:
                zref.extractall(os.path.dirname(zpath))
        except Exception as e:
            logger.error(f"Failed to extract {zpath}: {e}")

    # Read files
    context_text = ""
    for root_dir, _, files in os.walk(extracted_path):
        for f in files:
            if f.endswith(('.py', '.yaml', '.yml', '.md', '.txt', '.json')):
                fpath = os.path.join(root_dir, f)
                try:
                    with open(fpath, 'r', encoding='utf-8') as file_obj:
                        content = file_obj.read()
                        context_text += f"\n--- File: {os.path.relpath(fpath, extracted_path)} ---\n{content}\n"
                except Exception:
                    pass
                    
    if not context_text:
        return "No readable text or code files found."
    return context_text[:100000]

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
        self.graph = graph.compile()
        
    def _run_maker(self, state: MakerCheckerState):
        from src.agents.context_compressor.orchestrator import ContextCompressorAgent
        from src.core.config import settings
        
        context = state.get("messages", [])
        
        # 1. Identify if there's a path in the context to extract
        llm = ChatOpenAI(
            model=settings.LLM_MODEL_NAME,
            api_key=settings.LLM_API_KEY,
            temperature=0.0,
            base_url=settings.LLM_BASE_URL
        ).with_structured_output(PathExtraction)
        
        path_eval = llm.invoke([SystemMessage(content="Analyze the context and extract any file or directory paths mentioned. Ignore URLs.")] + context)
        
        extracted_content = ""
        if path_eval.has_path and path_eval.extracted_path:
            logger.info(f"Librarian extracting path: {path_eval.extracted_path}")
            extracted_content = extract_and_read_context(path_eval.extracted_path)
            
        feedback = state.get("feedback", "")
        worker_context = f"{context}\nExtracted File Content:\n{extracted_content}\nFeedback from previous run: {feedback}" if feedback else f"{context}\nExtracted File Content:\n{extracted_content}"
        
        # 2. Compress the context
        worker = ContextCompressorAgent()
        attempts = state.get("attempts", 0) + 1
        result = worker.execute(worker_context, "librarian_pm_loop")
        return {"worker_result": result, "attempts": attempts}

    def _run_validator(self, state: MakerCheckerState):
        from src.agents.agent_validator.orchestrator import AgentValidatorAgent
        validator = AgentValidatorAgent()
        
        validation = validator.execute(state["worker_result"], "librarian_pm_loop")
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
