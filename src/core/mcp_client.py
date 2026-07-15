import logging
import asyncio
from typing import Dict, Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langgraph.errors import GraphInterrupt

from src.core.security.proxy_delegation import proxy_loop

logger = logging.getLogger(__name__)

class PlatformMCPClient:
    """
    Platform as an MCP Client (For Agents).
    Dynamically loads MCP servers defined in the `project.yaml` and executes them on behalf of agents.
    Enforces RBAC and triggers JIT Supervisory Escalation for destructive actions.
    """
    def __init__(self, mcp_config: Dict[str, Any]):
        self.mcp_config = mcp_config

    async def execute_tool(self, server_name: str, tool_name: str, arguments: dict, session_id: str) -> str:
        if server_name not in self.mcp_config:
            return f"Error: Server {server_name} not found in project manifest."
            
        server_def = self.mcp_config[server_name]
        
        # Enforce RBAC and JIT Proxy Delegation
        if server_def.get("rbac_level") == "destructive_jit":
            logger.warning(f"JIT Escalation Required for tool {tool_name} on server {server_name}")
            
            # This halts the LangGraph and asks the proxy loop to queue an approval request
            request_id = await proxy_loop.request_jit_execution(
                agent_id=session_id, 
                action=f"{server_name}/{tool_name}", 
                payload=arguments
            )
            
            # The GraphInterrupt bubbles up to LangGraph to pause execution
            raise GraphInterrupt(f"JIT_APPROVAL_REQUIRED: {request_id}")

        # If readonly or approved, execute the tool
        cmd = server_def["command"]
        args = server_def.get("args", [])
        env = server_def.get("env", {})
        
        server_params = StdioServerParameters(command=cmd, args=args, env=env)
        
        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments=arguments)
                    if getattr(result, 'content', None):
                        return "\n".join([c.text for c in result.content if hasattr(c, 'text')])
                    return str(result)
        except Exception as e:
            logger.error(f"Failed to execute MCP tool: {e}")
            return f"Error executing MCP tool: {e}"
