"""
MCP Tool Service — manages MCP server discovery and tool execution.
"""
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class MCPToolService:
    """
    Manages MCP server listing and tool execution.
    Delegates to the PlatformMCPClient for actual tool calls.
    """

    def __init__(self):
        self._mcp_config: Optional[Dict[str, Any]] = None

    def _load_config(self) -> Dict[str, Any]:
        """
        Loads MCP server configurations from project manifest or environment.
        In production, this reads from the active project's project.yaml.
        """
        if self._mcp_config is not None:
            return self._mcp_config

        # Default platform-level MCP servers
        self._mcp_config = {
            "coreason-platform-mcp-server": {
                "command": "python",
                "args": ["-m", "src.core.mcp_server"],
                "transport": "stdio",
                "description": "Platform MCP Server — exposes workspace state to IDEs.",
                "tools": ["get_workspace_state"],
            }
        }
        return self._mcp_config

    def list_servers(self) -> List[Dict[str, Any]]:
        """List all configured MCP servers with their metadata."""
        config = self._load_config()
        servers = []
        for name, server_def in config.items():
            servers.append({
                "name": name,
                "transport": server_def.get("transport", "stdio"),
                "description": server_def.get("description", ""),
                "tools": server_def.get("tools", []),
            })
        return servers

    async def execute_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        session_id: str,
    ) -> Dict[str, Any]:
        """
        Execute an MCP tool via the PlatformMCPClient.
        """
        config = self._load_config()

        if server_name not in config:
            return {
                "status": "error",
                "detail": f"MCP server '{server_name}' not found. Available: {list(config.keys())}",
            }

        from src.core.mcp_client import PlatformMCPClient
        client = PlatformMCPClient(config)

        try:
            result = await client.execute_tool(server_name, tool_name, arguments, session_id)
            return {
                "status": "success",
                "server": server_name,
                "tool": tool_name,
                "result": result,
            }
        except Exception as e:
            logger.error(f"MCP tool execution failed: {e}")
            return {
                "status": "error",
                "server": server_name,
                "tool": tool_name,
                "detail": str(e),
            }
