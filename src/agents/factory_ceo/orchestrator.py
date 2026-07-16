from typing import Any, Dict, TypedDict
import uuid
import os
import yaml
from src.core.base_agent import DeepAgent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig

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

def evaluate_context(state: OrchestratorCeoState) -> dict:
    """
    Evaluates if the context is saturated enough to delegate.
    """
    from src.core.config import settings
    llm = ChatOpenAI(
        model=settings.LLM_MODEL_NAME,
        api_key=settings.LLM_API_KEY,
        temperature=settings.LLM_TEMPERATURE,
        base_url=settings.LLM_BASE_URL
    )
    
    messages = state.get("messages", [])
    
    system_prompt = SystemMessage(content="""You are an expert orchestrator. 
Evaluate if the user's intent contains enough information to build the requested multi-agent topology.
If the user provided a file path that has NOT yet been summarized by the librarian, you MUST reply with the exact word 'DELEGATE_TO_LIBRARIAN' to have the librarian index it.
If the architectural summary from the librarian is present and fully resolves the topology, reply with the exact word 'SATURATED'.
If you need more information from the user to resolve ambiguities, reply with 'INTERROGATE'.""")

    response = llm.invoke([system_prompt] + messages)
    content = str(response.content).upper()
    
    if "DELEGATE_TO_LIBRARIAN" in content:
        routing = "delegate_to_librarian"
        is_saturated = False
    elif "SATURATED" in content:
        routing = "delegate"
        is_saturated = True
    else:
        routing = "interrogate"
        is_saturated = False
        
    return {"messages": [response], "routing": routing, "is_saturated": is_saturated}

def delegate_to_librarian(state: OrchestratorCeoState, config: RunnableConfig) -> dict:
    """
    Delegates path and file processing to the librarian_pm.
    """
    logger.info("Delegating codebase extraction to librarian_pm.")
    from src.agents.librarian_pm.orchestrator import LibrarianPmAgent
    # Passing control to sub-agent
    pm = LibrarianPmAgent()
    if hasattr(pm, 'execute'):
        session_id = config.get("configurable", {}).get("thread_id")
        result = pm.execute(state, session_id=session_id)
        return {"messages": [SystemMessage(content=f"Librarian Summary: {result}")]}
    return {"messages": [SystemMessage(content="librarian_pm executed successfully.")]}

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
    Asks user for more context based on missing architectural details.
    """
    from src.core.config import settings
    llm = ChatOpenAI(
        model=settings.LLM_MODEL_NAME,
        api_key=settings.LLM_API_KEY,
        temperature=settings.LLM_TEMPERATURE,
        base_url=settings.LLM_BASE_URL
    )
    messages = state.get("messages", [])
    prompt = SystemMessage(content="Based on the current context, what specific architectural question should we ask the user to clarify the agent topology? Return only the question.")
    response = llm.invoke([prompt] + messages)
    # The returned message acts as a 'break' out of the graph to ask the user
    return {"messages": [SystemMessage(content=response.content)]}

def route_evaluation(state: OrchestratorCeoState) -> str:
    return state.get("routing", "interrogate")

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
        self.graph_builder.add_node("delegate_to_librarian", delegate_to_librarian)
        self.graph_builder.add_node("delegate", delegate_to_pm)
        self.graph_builder.add_node("interrogate", interrogate_user)
        
        self.graph_builder.set_entry_point("interceptor")
        self.graph_builder.add_edge("interceptor", "evaluator")
        self.graph_builder.add_conditional_edges(
            "evaluator",
            route_evaluation,
            {"delegate_to_librarian": "delegate_to_librarian", "delegate": "delegate", "interrogate": "interrogate"}
        )
        self.graph_builder.add_edge("delegate_to_librarian", "evaluator")
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
