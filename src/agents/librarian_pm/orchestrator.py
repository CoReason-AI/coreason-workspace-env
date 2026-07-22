import os
import uuid
import yaml
import logging
import zipfile
import glob
from typing import Any
from src.core.base_agent import DeepAgent
from deepagents.graph import DeepAgentState
from langchain_core.tools import tool

from langchain_core.runnables import RunnableLambda
from deepagents.graph import create_deep_agent

logger = logging.getLogger(__name__)

@tool
def extract_and_read_context(path: str) -> str:
    """Extracts zip files in the given directory path. Subagents must use native BackendProtocol tools (like ls and read_file) to explore the codebase after extraction."""
    extracted_path = os.path.abspath(path.strip('\'"'))
    if not os.path.exists(extracted_path):
        return f"Path does not exist: {extracted_path}"
    
    nested_zips = glob.glob(os.path.join(extracted_path, '**', '*.zip'), recursive=True)
    for zpath in nested_zips:
        try:
            with zipfile.ZipFile(zpath, 'r') as zref:
                zref.extractall(os.path.dirname(zpath))
        except Exception as e:
            logger.error(f"Failed to extract {zpath}: {e}")

    return f"Extraction complete. The directory {extracted_path} is ready. Use native `ls`, `grep`, and `read_file` tools to explore the codebase."

class LibrarianPmAgent(DeepAgent):
    """
    Project Manager for orchestrating the Knowledge Base pipeline via create_deep_agent.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        yaml_path = os.path.join(os.path.dirname(__file__), "agent.yaml")
        self.agent_spec = {}
        if os.path.exists(yaml_path):
            with open(yaml_path, "r", encoding="utf-8") as f:
                self.agent_spec = yaml.safe_load(f)
                
        base_prompt = self.agent_spec.get("system_prompt", "You are an autonomous Librarian PM.")
        pm_prompt = """
You are an autonomous PM running a Knowledge Base indexing pipeline.
You have one subagent exposed as a tool: context_compressor.
You also have the tool `extract_and_read_context` to read files from the filesystem.

Step 1: If the user provides a path, use `extract_and_read_context` to extract it.
Step 2: Delegate the context (and any extracted file contents) to `context_compressor`.
Once complete, return the final Markdown response.
"""
        self.system_prompt = f"{base_prompt}\n{pm_prompt}"

    def execute(self, context: Any, session_id: str = None, config: dict = None) -> str:
        """
        Executes pipeline using a ReAct deep agent.
        """
        logger.info(f"[{session_id}] LibrarianPM initiating ReAct deep agent pipeline.")
        
        from src.agents.context_compressor.orchestrator import ContextCompressorAgent
        
        subagents = [
            {
                "name": "context_compressor",
                "description": "Compresses full codebase text into a technical summary.",
                "runnable": RunnableLambda(lambda inputs, c: ContextCompressorAgent().execute(inputs, "librarian_pm_loop"))
            }
        ]

        internal_thread_id = f"{session_id or str(uuid.uuid7())}-librarian"
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
                tools=[extract_and_read_context],
                checkpointer=checkpointer
            )
            
            result = graph.invoke(initial_state, config=internal_config)
            
        final_message = result.get("messages", [])[-1].content if result.get("messages") else "FAILURE: No output produced."
        return final_message
