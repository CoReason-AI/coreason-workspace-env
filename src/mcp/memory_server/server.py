import os
import sys
import json
import asyncio
import logging

try:
    import asyncpg
except ImportError:
    # Just a placeholder if not installed, tests should mock or install it
    asyncpg = None

# Configure logging to stderr (stdio is used for MCP)
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s', stream=sys.stderr)
logger = logging.getLogger("memory_server")

DB_DSN = os.environ.get("POSTGRES_DSN", "postgresql://admin:password@localhost:5432/knowledge_db")

async def init_db(pool):
    """Initialize the pgvector extension and table."""
    async with pool.acquire() as conn:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_chunks (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                metadata JSONB,
                embedding vector(1536)
            );
        """)

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
            chunks = params.get("chunks", [])
            metadata = params.get("metadata", {})
            inserted = 0
            
            if not asyncpg:
                return json.dumps({"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32603, "message": "asyncpg not installed"}})
                
            async with pool.acquire() as conn:
                for chunk in chunks:
                    vec = await dummy_embed(chunk)
                    await conn.execute(
                        "INSERT INTO knowledge_chunks (content, metadata, embedding) VALUES ($1, $2, $3::vector)",
                        chunk, json.dumps(metadata), str(vec)
                    )
                    inserted += 1
            
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"status": "success", "chunks_inserted": inserted}
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
                    "SELECT id, content, metadata FROM knowledge_chunks ORDER BY embedding <=> $1::vector LIMIT $2",
                    str(vec), top_k
                )
            
            results = []
            for r in rows:
                results.append({
                    "id": r['id'],
                    "content": r['content'],
                    "metadata": json.loads(r['metadata']) if r['metadata'] else {}
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
