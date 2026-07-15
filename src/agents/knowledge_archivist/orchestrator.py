import logging
import json
from typing import Any
from langgraph.graph import StateGraph, START, END
from deepagents import DeepAgent

from src.core.db import get_db_pool
from src.core.schemas.epistemic_firewall import LibrarianRoutingState
from src.core.services import mcp_tool_service

from langchain_openai import ChatOpenAI
from coreason_manifest.spec.ontology import (
    SemanticNodeState,
    CausalDirectedEdgeState,
    DocumentKnowledgeGraphManifest,
    CognitiveDeliberativeEnvelopeState
)

logger = logging.getLogger(__name__)

async def ingestion_node(state: LibrarianRoutingState) -> dict[str, Any]:
    """
    Pulls raw text, runs structural decoding, and pushes it via MCP.
    """
    proxy_cid = state.proxy.proxy_cid
    
    # 1. Pull raw text from WORM Postgres table
    raw_text = None
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT raw_payload FROM epistemic_quarantine_snapshots WHERE snapshot_id = $1",
                proxy_cid
            )
            if row:
                raw_text = row["raw_payload"]
    except Exception as e:
        logger.error(f"Failed to fetch snapshot {proxy_cid}: {e}")
        return {"directives": f"Error fetching snapshot: {e}"}

    if not raw_text:
        return {"directives": "No raw text found in quarantine."}

    # 2. Use structured decoding
    logger.info("Extracting DocumentKnowledgeGraphManifest via structured decoding.")
    llm = ChatOpenAI(
        model="nvidia/nemotron-3-nano-30b-a3b:free",
        api_key="sovereign-key-placeholder",
        temperature=0.0
    )
    structured_llm = llm.with_structured_output(CognitiveDeliberativeEnvelopeState[DocumentKnowledgeGraphManifest])
    envelope = await structured_llm.ainvoke(f"Extract nodes and edges from: {raw_text}")
    
    # 3. Package and execute mcp_write_vectors
    logger.info("Writing vectors to pgvector via memory_server MCP tool.")
    try:
        await mcp_tool_service.execute_tool(
            server_name="memory_server",
            tool_name="mcp_write_vectors",
            arguments={
                "snapshot_id": proxy_cid,
                "manifest": envelope.payload.model_dump_json()
            }
        )
    except Exception as e:
        logger.error(f"Failed to write vectors: {e}")
        return {"directives": f"MCP execution failed: {e}"}

    return {"directives": "Ingestion successful. Vectors written."}


workflow = StateGraph(LibrarianRoutingState)

workflow.add_node("ingestion", ingestion_node)
workflow.add_edge(START, "ingestion")
workflow.add_edge("ingestion", END)

compiled_archivist_graph = workflow.compile()


class KnowledgeArchivistAgent(DeepAgent):
    """
    Orchestrator for knowledge_archivist.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
