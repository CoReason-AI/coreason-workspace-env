import os
import sys
import json
import asyncio
import logging

try:
    import asyncpg
except ImportError:
    # Memory server implementation required for integration.
    asyncpg = None

# Configure logging to stderr (stdio is used for MCP)
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s', stream=sys.stderr)
from src.core.config import settings

logger = logging.getLogger("memory_server")

DB_DSN = (
    f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

async def init_db(pool):
    """
    Initialize connection pool.
    Schema definition is now handled by Alembic migrations.
    """
    pass

async def dummy_embed(text: str) -> list[float]:
    """
    A dummy embedding function for demonstration.
    In a real scenario, this would call OpenAI API or a local sentence transformer.
    """
    # Return a dummy 1536-dimensional vector for testing purposes.
    # We hash the text lightly to produce some deterministic variance.
    val = float(sum(ord(c) for c in text)) / 10000.0
    return [val] * 1536

async def handle_request(request_str: str, pool) -> str:
    """Handle incoming JSON-RPC requests."""
    try:
        req = json.loads(request_str)
        method = req.get("method")
        params = req.get("params", {})
        msg_id = req.get("id")

        if method == "mcp_write_vectors":
            manifest = params.get("manifest", {})
            
            # --- FIX: Parse JSON string if sent by Pydantic model_dump_json() ---
            if isinstance(manifest, str):
                try:
                    manifest = json.loads(manifest)
                except json.JSONDecodeError:
                    return json.dumps({"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32602, "message": "Invalid JSON in manifest"}})

            nodes = manifest.get("nodes", [])
            edges = manifest.get("edges", [])
            inserted_nodes = 0
            inserted_edges = 0
            
            if not asyncpg:
                return json.dumps({"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32603, "message": "asyncpg not installed"}})
                
            async with pool.acquire() as conn:
                for node in nodes:
                    vec = await dummy_embed(node.get("content", ""))
                    await conn.execute(
                        "INSERT INTO knowledge_nodes (node_id, label, content, embedding) VALUES ($1, $2, $3, $4::vector) ON CONFLICT DO NOTHING",
                        node.get("node_id"), node.get("label"), node.get("content"), str(vec)
                    )
                    inserted_nodes += 1
                for edge in edges:
                    await conn.execute(
                        "INSERT INTO knowledge_edges (source_id, target_id, relationship) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
                        edge.get("source_id"), edge.get("target_id"), edge.get("relationship")
                    )
                    inserted_edges += 1
            
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"status": "success", "nodes_inserted": inserted_nodes, "edges_inserted": inserted_edges}
            })

        elif method == "mcp_query_vectors":
            query = params.get("query", "")
            top_k = params.get("top_k", 3)
            
            if not asyncpg:
                return json.dumps({"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32603, "message": "asyncpg not installed"}})
                
            vec = await dummy_embed(query)
            
            async with pool.acquire() as conn:
                # <=> is cosine distance in pgvector
                rows = await conn.fetch(
                    "SELECT node_id, label, content FROM knowledge_nodes ORDER BY embedding <=> $1::vector LIMIT $2",
                    str(vec), top_k
                )
            
            results = []
            for r in rows:
                results.append({
                    "node_id": r['node_id'],
                    "label": r['label'],
                    "content": r['content']
                })
                
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"matches": results}
            })

        else:
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method {method} not found"}
            })

    except Exception as e:
        logger.error(f"Error handling request: {e}", exc_info=True)
        return json.dumps({
            "jsonrpc": "2.0",
            "id": req.get("id"),
            "error": {"code": -32603, "message": str(e)}
        })

async def main():
    logger.info("Starting memory_server MCP over stdio...")
    
    if not asyncpg:
        logger.warning("asyncpg is not installed. Database operations will fail.")
        pool = None
    else:
        try:
            pool = await asyncpg.create_pool(DB_DSN)
            await init_db(pool)
            logger.info("Connected to pgvector database.")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            pool = None

    loop = asyncio.get_running_loop()
    
    while True:
        # Read from stdin asynchronously
        line = await loop.run_in_executor(None, sys.stdin.readline)
        if not line:
            break
        
        response = await handle_request(line, pool)
        
        # Write to stdout
        sys.stdout.write(response + "\n")
        sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(main())
