import json
import logging
from typing import Dict, Any

from mcp.server.stdio import stdio_server
from mcp.server import Server

logger = logging.getLogger(__name__)

class PlatformMCPServer:
    """
    Platform as an MCP Server (For Human IDEs).
    Exposes the active Project Workspace (VFS and LangGraph state) to external tools like Cursor.
    """
    def __init__(self):
        self.server = Server("coreason-platform-mcp-server")
        self._register_tools()

    def _register_tools(self):
        @self.server.list_tools()
        async def handle_list_tools() -> list:
            return [
                {
                    "name": "get_workspace_state",
                    "description": "Returns the current LangGraph state for the active project.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string"}
                        },
                        "required": ["session_id"]
                    }
                }
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list:
            if name == "get_workspace_state":
                session_id = arguments["session_id"]
                tenant_id = arguments.get("tenant_id", "default_tenant")
                try:
                    from src.core.db import get_db_pool
                    import asyncio
                    # Connect to real Postgres checkpointer with tenant isolation
                    pool = await get_db_pool()
                    async with pool.acquire() as conn:
                        records = await conn.fetch("SELECT state FROM langgraph_state WHERE thread_id = $1 AND tenant_id = $2 ORDER BY id DESC LIMIT 1", session_id, tenant_id)
                        if records:
                            state = records[0]['state']
                        else:
                            state = {"status": "NO_STATE_FOUND"}
                except Exception as e:
                    state = {"status": "ERROR", "message": str(e)}
                return [{"type": "text", "text": json.dumps(state)}]
            raise ValueError(f"Unknown tool: {name}")

    async def run(self):
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, self.server.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    server = PlatformMCPServer()
    asyncio.run(server.run())
