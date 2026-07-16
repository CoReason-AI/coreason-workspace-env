from typing import Any, Dict, TypedDict
import uuid
import os
import yaml
from src.core.base_agent import DeepAgent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

from src.core.ontology import (
    EpistemicQuarantineSnapshot,
    EpistemicProxyState,
    OrchestratorCeoState
)
from src.core.services.worm_storage import persist_quarantine_snapshot

import logging
logger = logging.getLogger(__name__)

async def epistemic_interceptor_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    LangGraph Node that physically intercepts large raw human transcripts
    BEFORE they enter the factory_ceo's context window.
    """
    raw_payload = state.get("raw_transcript")
    
    if raw_payload:
        snapshot = EpistemicQuarantineSnapshot(
            snapshot_id=str(uuid.uuid7()),
            raw_payload=raw_payload
        )
        
        # Persist to WORM Postgres table via core service (Body infrastructure)
        await persist_quarantine_snapshot(snapshot)
        
        proxy = EpistemicProxyState(
            proxy_cid=snapshot.snapshot_id,
            structural_type="HumanTranscript"
        )
        
        return {
            "raw_transcript": None,
            "epistemic_proxy": proxy
        }
        
    return {}

from langchain_core.tools import tool
import zipfile
import glob

@tool
def extract_and_read_context(path: str) -> str:
    """Extracts zip files and reads all text/code files in the given directory path to provide the codebase context."""
    extracted_path = os.path.abspath(path)
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

def evaluate_context(state: OrchestratorCeoState) -> dict:
    """
    Evaluates if the context is saturated enough to delegate.
    Uses tools if necessary.
    """
    from src.core.config import settings
    llm = ChatOpenAI(
        model=settings.LLM_MODEL_NAME,
        api_key=settings.LLM_API_KEY,
        temperature=settings.LLM_TEMPERATURE,
        base_url=settings.LLM_BASE_URL
    )
    llm_with_tools = llm.bind_tools([extract_and_read_context])
    
    # We pass the full message history so the LLM sees previous tool outputs
    messages = state.get("messages", [])
    
    system_prompt = SystemMessage(content="""You are an expert orchestrator. 
Evaluate if the user's intent contains enough information and code context to build the requested multi-agent topology.
If the user provided a file path, you MUST call the `extract_and_read_context` tool to read the codebase.
If you have all the necessary information, reply with the exact word 'YES'.
If you need more information from the user (and no path was provided), reply with 'NO'.""")

    response = llm_with_tools.invoke([system_prompt] + messages)
    
    is_saturated = "YES" in str(response.content).upper() if response.content else False
    
    return {"messages": [response], "is_saturated": is_saturated}

from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import ToolNode

def delegate_to_pm(state: OrchestratorCeoState, config: RunnableConfig) -> dict:
    """
    Delegates saturated context to the agent_pm.
    """
    logger.info("Context saturated. Delegating to agent_pm.")
    from src.agents.agent_pm.orchestrator import AgentPmAgent
    # Passing control to sub-agent
    pm = AgentPmAgent()
    if hasattr(pm, 'execute'):
        session_id = config.get("configurable", {}).get("thread_id")
        result = pm.execute(state, session_id=session_id, config=config)
        return {"messages": [SystemMessage(content=f"Delegation result: {result}")]}
    return {"messages": [SystemMessage(content="agent_pm executed successfully.")]}

def interrogate_user(state: OrchestratorCeoState) -> dict:
    """
    Asks user for more context.
    """
    return {"messages": [SystemMessage(content="Please provide more detailed requirements for your agent.")]}

def route_evaluation(state: OrchestratorCeoState) -> str:
    messages = state.get("messages", [])
    if messages and hasattr(messages[-1], "tool_calls") and messages[-1].tool_calls:
        return "tools"
    if state.get("is_saturated"):
        return "delegate"
    return "interrogate"

class FactoryCeoAgent(DeepAgent):
    """
    State Machine Orchestrator for factory_ceo.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        yaml_path = os.path.join(os.path.dirname(__file__), "agent.yaml")
        if os.path.exists(yaml_path):
            with open(yaml_path, "r", encoding="utf-8") as f:
                self.agent_spec = yaml.safe_load(f)
                
        self.graph_builder = StateGraph(OrchestratorCeoState)
        self.graph_builder.add_node("interceptor", epistemic_interceptor_node)
        self.graph_builder.add_node("evaluator", evaluate_context)
        self.graph_builder.add_node("tools", ToolNode([extract_and_read_context]))
        self.graph_builder.add_node("delegate", delegate_to_pm)
        self.graph_builder.add_node("interrogate", interrogate_user)
        
        self.graph_builder.set_entry_point("interceptor")
        self.graph_builder.add_edge("interceptor", "evaluator")
        self.graph_builder.add_conditional_edges(
            "evaluator",
            route_evaluation,
            {"tools": "tools", "delegate": "delegate", "interrogate": "interrogate"}
        )
        self.graph_builder.add_edge("tools", "evaluator")
        self.graph_builder.add_edge("delegate", END)
        self.graph_builder.add_edge("interrogate", END)
        
        self.graph = self.graph_builder.compile()

    async def execute(self, context: dict, session_id: str = None) -> Any:
        from src.core.services.observability_service import ObservabilityService
        obs = ObservabilityService()
        langfuse_cb = obs.get_langfuse_callback(session_id)
        
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        async with AsyncPostgresSaver.from_conn_string(obs.pg_dsn) as checkpointer:
            await checkpointer.setup()
            
            graph_with_checkpointer = self.graph_builder.compile(checkpointer=checkpointer)
            
            config = {
                "configurable": {"thread_id": session_id or str(uuid.uuid7())}
            }
            if langfuse_cb:
                config["callbacks"] = [langfuse_cb]
                
            return await graph_with_checkpointer.ainvoke(context, config=config)
