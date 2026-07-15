import logging
from typing import Any
from langgraph.graph import StateGraph, START, END
from deepagents import DeepAgent

from src.core.schemas.epistemic_firewall import LibrarianRoutingState
from src.core.services import mcp_tool_service
from src.core.schemas.knowledge_receipt import KnowledgeReceipt, ProvenanceCitation

from langchain_openai import ChatOpenAI
from coreason_manifest.spec.ontology import CognitiveDeliberativeEnvelopeState

logger = logging.getLogger(__name__)

async def retrieval_node(state: LibrarianRoutingState) -> dict[str, Any]:
    """
    Executes a vector search and synthesizes a strict KnowledgeReceipt.
    """
    query = state.directives or "Provide historical context."
    logger.info(f"Knowledge Consultant executing query: {query}")
    
    # 1. Execute mcp_query_vectors tool to fetch matching semantic context
    logger.info("Querying pgvector via memory_server MCP tool.")
    try:
        context = await mcp_tool_service.execute_tool(
            server_name="memory_server",
            tool_name="mcp_query_vectors",
            arguments={"query": query, "top_k": 5}
        )
    except Exception as e:
        logger.error(f"Failed to query vectors: {e}")
        return {"directives": f"MCP retrieval failed: {e}"}

    # 2. Implement synthesis using the LLM restricted to CognitiveDeliberativeEnvelopeState[KnowledgeReceipt]
    logger.info("Synthesizing KnowledgeReceipt with ProvenanceCitation mapping back to the exact node ID.")
    from src.core.config import settings
    llm = ChatOpenAI(
        model=settings.LLM_MODEL_NAME,
        api_key=settings.LLM_API_KEY,
        temperature=settings.LLM_TEMPERATURE,
        base_url=settings.LLM_BASE_URL
    )
    structured_llm = llm.with_structured_output(CognitiveDeliberativeEnvelopeState[KnowledgeReceipt])
    envelope = await structured_llm.ainvoke(f"Context: {context}\n\nQuery: {query}")

    return {
        "directives": "Retrieval and synthesis complete.",
        "receipt": envelope.payload.model_dump_json()
    }

workflow = StateGraph(LibrarianRoutingState)
workflow.add_node("retrieval", retrieval_node)
workflow.add_edge(START, "retrieval")
workflow.add_edge("retrieval", END)

compiled_consultant_graph = workflow.compile()


class KnowledgeConsultantAgent(DeepAgent):
    """
    Orchestrator for knowledge_consultant.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
