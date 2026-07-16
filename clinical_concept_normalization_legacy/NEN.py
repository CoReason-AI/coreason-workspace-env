import os
import sys
import json
import asyncio
import datetime
from contextlib import AsyncExitStack
from mcp import ClientSession
from mcp.client.sse import sse_client

# Constants
MODERNBERT_URL = "https://demo.coreason.ai:8994/sse"
SAPBERT_URL = "https://demo.coreason.ai:8993/sse"
DEFAULT_BEARER_TOKEN = "aee2dc865a7ff6307af88ccd70029ab378e7dbcd8371a7f5c0c95e36589995c5"
SIMILARITY_THRESHOLD = 0.80

async def process_nen_tagging(clinical_chunks, session):
    """Performs Named Entity Normalization (NEN) on clinical chunks using an active MCP session."""
    tagged_chunks = []
    
    for chunk in clinical_chunks:
        verbatim = chunk.get("verbatim_chunk")
        concept_type = chunk.get("concept_type")
        is_negated = chunk.get("is_negated", False)
        is_historical = chunk.get("is_historical", False)
        
        if not verbatim:
            continue
            
        umls_cui = None
        dense_vector_match = False
        
        # Step 2: Dense Vector Embedding Match
        if session:
            try:
                response = await session.call_tool(
                    "semantic_search_umls", 
                    {"term": verbatim.lower(), "top_k": 5}
                )
                results = json.loads(response.content[0].text) if response.content else []
                
                if results:
                    best_match = results[0]
                    conf = float(best_match.get("similarity", best_match.get("similarity_score", best_match.get("score", 0.0))))
                    if conf >= SIMILARITY_THRESHOLD:
                        umls_cui = best_match.get("cui")
                        dense_vector_match = True
            except Exception as e:
                sys.stderr.write(f"Warning: Dense vector search failed for '{verbatim}': {e}\n")
                
            # Step 4: Fallback Text Search (if dense search is unsuccessful or below threshold)
            if not umls_cui:
                try:
                    response = await session.call_tool(
                        "search_umls_concept", 
                        {"term": verbatim.lower()}
                    )
                    results_text = json.loads(response.content[0].text) if response.content else []
                    
                    if isinstance(results_text, list) and results_text:
                        umls_cui = results_text[0].get("cui")
                    elif isinstance(results_text, dict) and not results_text.get("error"):
                        umls_cui = results_text.get("cui")
                except Exception as e:
                    sys.stderr.write(f"Warning: Fallback text search failed for '{verbatim}': {e}\n")
                
        # Refusal Predicate: If both fail, tag as null
        if not umls_cui:
            umls_cui = None
            
        tagged_chunks.append({
            "verbatim_chunk": verbatim,
            "concept_type": concept_type,
            "is_negated": is_negated,
            "is_historical": is_historical,
            "umls_cui": umls_cui,
            "dense_vector_match": dense_vector_match
        })
        
    # Provenance Receipt metadata
    provenance_receipts = {
        "database_version": "UMLS 2026AB",
        "retrieval_timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    return {
        "tagged_chunks": tagged_chunks,
        "provenance_receipts": provenance_receipts
    }

async def connect_mcp_session(stack, url, headers):
    """Attempts to connect to an MCP server at the given URL."""
    read_stream, write_stream = await stack.enter_async_context(
        sse_client(url, headers=headers, timeout=10.0)
    )
    session = await stack.enter_async_context(
        ClientSession(read_stream, write_stream)
    )
    await session.initialize()
    return session

async def main():
    # Load parameters from environment or default
    modernbert_url = os.environ.get("MODERNBERT_MCP_URL", MODERNBERT_URL)
    sapbert_url = os.environ.get("SAPBERT_MCP_URL", SAPBERT_URL)
    bearer_token = os.environ.get("UMLS_BEARER_TOKEN", DEFAULT_BEARER_TOKEN)
    
    # Read input payload
    input_text = None
    if len(sys.argv) > 1:
        arg = sys.argv[1].strip()
        if arg.startswith("{") or arg.startswith("["):
            input_text = arg
        elif os.path.exists(arg):
            with open(arg, "r", encoding="utf-8") as f:
                input_text = f.read()
    elif not sys.stdin.isatty():
        input_text = sys.stdin.read().strip()
        
    if not input_text:
        sys.stderr.write("Error: No input JSON payload provided. Please provide clinical_chunks via stdin or CLI argument.\n")
        sys.exit(1)
        
    try:
        parsed = json.loads(input_text)
        if isinstance(parsed, list):
            input_payload = {"clinical_chunks": parsed}
        else:
            input_payload = parsed
    except Exception as e:
        sys.stderr.write(f"Error parsing input JSON: {e}\n")
        sys.exit(1)
            
    # Establish connection headers
    headers = {}
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
        headers["X-Accel-Buffering"] = "no"
        
    session = None
    async with AsyncExitStack() as stack:
        # Try connecting to ModernBERT primary server
        sys.stderr.write(f"Connecting to primary ModernBERT server at: {modernbert_url}...\n")
        try:
            session = await connect_mcp_session(stack, modernbert_url, headers)
            sys.stderr.write("Connected to primary ModernBERT server successfully.\n")
        except Exception as e_modern:
            sys.stderr.write(f"Warning: Primary ModernBERT server failed ({e_modern}).\n")
            # Try connecting to SapBERT fallback server
            sys.stderr.write(f"Attempting failover to secondary SapBERT server at: {sapbert_url}...\n")
            try:
                session = await connect_mcp_session(stack, sapbert_url, headers)
                sys.stderr.write("Connected to secondary SapBERT server successfully.\n")
            except Exception as e_sap:
                sys.stderr.write(f"Warning: Secondary SapBERT server failed ({e_sap}). Running offline.\n")
                session = None
                
        # Execute tagging (works offline as well, returning null as per Refusal Predicate)
        output = await process_nen_tagging(input_payload.get("clinical_chunks", []), session)
        print(json.dumps(output, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
