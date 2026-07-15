import logging
from typing import Any
from langgraph.graph import StateGraph, START, END
from deepagents import DeepAgent
from src.core.schemas.epistemic_firewall import LibrarianRoutingState

# 1. Import the compiled graphs from the sub-agents
from src.agents.knowledge_archivist.orchestrator import compiled_archivist_graph
from src.agents.knowledge_consultant.orchestrator import compiled_consultant_graph

logger = logging.getLogger(__name__)

def router_node(state: LibrarianRoutingState) -> dict[str, Any]:
    """Node that evaluates the routing state."""
    logger.info(f"Librarian routing proxy: {state.proxy.proxy_cid}")
    return {}

def route_task(state: LibrarianRoutingState) -> str:
    """
    Conditional edge to determine if payload is an ingestion task or retrieval task.
    """
    if state.proxy.structural_type == "HumanTranscript":
        return "knowledge_archivist"
    return "knowledge_consultant"

# 2. Replace stubs with actual Sub-Graph invocations
async def knowledge_archivist_node(state: LibrarianRoutingState) -> dict[str, Any]:
    logger.info("Librarian PM: Delegating to Knowledge Archivist...")
    # Invoke the actual archivist graph
    result = await compiled_archivist_graph.ainvoke(state)
    return {"directives": result.get("directives", "Archivist execution completed.")}

async def knowledge_consultant_node(state: LibrarianRoutingState) -> dict[str, Any]:
    logger.info("Librarian PM: Delegating to Knowledge Consultant...")
    # Invoke the actual consultant graph
    result = await compiled_consultant_graph.ainvoke(state)
    return {"directives": result.get("directives", "Consultant execution completed.")}

workflow = StateGraph(LibrarianRoutingState)
workflow.add_node("router", router_node)
workflow.add_node("knowledge_archivist", knowledge_archivist_node)
workflow.add_node("knowledge_consultant", knowledge_consultant_node)

workflow.add_edge(START, "router")
workflow.add_conditional_edges(
    "router",
    route_task,
    {
        "knowledge_archivist": "knowledge_archivist",
        "knowledge_consultant": "knowledge_consultant"
    }
)
workflow.add_edge("knowledge_archivist", END)
workflow.add_edge("knowledge_consultant", END)

compiled_librarian_graph = workflow.compile()

class LibrarianPmAgent(DeepAgent):
    """
    Orchestrator for librarian_pm.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
