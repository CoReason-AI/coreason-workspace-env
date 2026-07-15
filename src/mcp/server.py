"""
CoReason Platform MCP Server — exposes all platform operations as MCP tools.
Enables upstream AI agents, IDEs, and orchestrators to control the platform natively.

All tools delegate to src.core.services (same shared business logic as API/CLI/SDK).

Usage:
    python -m src.mcp.server
"""
import json
import asyncio
import logging
import uuid
from typing import Any

from mcp.server.stdio import stdio_server
from mcp.server import Server

logger = logging.getLogger(__name__)


def _build_server() -> Server:
    """Build and configure the MCP Server with all platform tools."""
    server = Server("coreason-platform")

    @server.list_tools()
    async def handle_list_tools() -> list:
        return [
            {
                "name": "health_check",
                "description": "Check platform health — Postgres, Redis connectivity and version info.",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
            },
            {
                "name": "list_projects",
                "description": "List all projects in the workspace.",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
            },
            {
                "name": "create_project",
                "description": "Create a new project.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Unique project name"},
                        "description": {"type": "string", "description": "Project description"},
                    },
                    "required": ["name"],
                },
            },
            {
                "name": "get_project",
                "description": "Fetch a single project by ID.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"project_id": {"type": "string"}},
                    "required": ["project_id"],
                },
            },
            {
                "name": "delete_project",
                "description": "Delete a project by ID.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"project_id": {"type": "string"}},
                    "required": ["project_id"],
                },
            },
            {
                "name": "list_agents",
                "description": "List all agents in the factory with their metadata.",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
            },
            {
                "name": "get_agent",
                "description": "Get a specific agent's manifest and metadata.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"agent_name": {"type": "string"}},
                    "required": ["agent_name"],
                },
            },
            {
                "name": "execute_agent",
                "description": "Trigger a LangGraph execution flow for a specified agent.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "agent_name": {"type": "string"},
                        "user_id": {"type": "string"},
                        "tenant_id": {"type": "string"},
                        "payload": {"type": "object"},
                    },
                    "required": ["agent_name", "user_id", "tenant_id"],
                },
            },
            {
                "name": "list_mcp_servers",
                "description": "List connected MCP servers and their tools.",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
            },
            {
                "name": "execute_mcp_tool",
                "description": "Execute a tool on a connected MCP server.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "server_name": {"type": "string"},
                        "tool_name": {"type": "string"},
                        "arguments": {"type": "object"},
                        "session_id": {"type": "string"},
                    },
                    "required": ["server_name", "tool_name"],
                },
            },
            {
                "name": "generate_docs",
                "description": "Generate an MkDocs scaffold with config and markdown pages.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workspace_path": {"type": "string"},
                        "site_name": {"type": "string"},
                        "pages": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "filename": {"type": "string"},
                                    "content": {"type": "string"},
                                },
                                "required": ["title", "filename", "content"],
                            },
                        },
                    },
                    "required": ["workspace_path", "site_name", "pages"],
                },
            },
        ]

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list:
        result = await _dispatch_tool(name, arguments)
        return [{"type": "text", "text": json.dumps(result, default=str)}]

    return server


async def _dispatch_tool(name: str, args: dict) -> Any:
    """Dispatch MCP tool calls to the shared service layer."""
    from dotenv import load_dotenv
    load_dotenv()

    if name == "health_check":
        from src.core.services import health_service
        return await health_service.check()

    elif name == "list_projects":
        from src.core.services import project_service
        return {"projects": await project_service.list_projects()}

    elif name == "create_project":
        from src.core.services import project_service
        project = await project_service.create_project(
            project_id=str(uuid.uuid7()),
            name=args["name"],
            description=args.get("description", ""),
        )
        return {"status": "created", "project": project}

    elif name == "get_project":
        from src.core.services import project_service
        project = await project_service.get_project(args["project_id"])
        return {"project": project} if project else {"error": "Not found"}

    elif name == "delete_project":
        from src.core.services import project_service
        deleted = await project_service.delete_project(args["project_id"])
        return {"status": "deleted"} if deleted else {"error": "Not found"}

    elif name == "list_agents":
        from src.core.services import agent_service
        return {"agents": agent_service.list_agents()}

    elif name == "get_agent":
        from src.core.services import agent_service
        agent = agent_service.get_agent(args["agent_name"])
        return {"agent": agent} if agent else {"error": "Not found"}

    elif name == "execute_agent":
        from src.core.services import agent_service
        return await agent_service.execute_agent(
            agent_name=args["agent_name"],
            payload=args.get("payload", {}),
            user_id=args["user_id"],
            tenant_id=args["tenant_id"],
        )

    elif name == "list_mcp_servers":
        from src.core.services import mcp_tool_service
        return {"servers": mcp_tool_service.list_servers()}

    elif name == "execute_mcp_tool":
        from src.core.services import mcp_tool_service
        return await mcp_tool_service.execute_tool(
            server_name=args["server_name"],
            tool_name=args["tool_name"],
            arguments=args.get("arguments", {}),
            session_id=args.get("session_id", "mcp-session"),
        )

    elif name == "generate_docs":
        from src.core.services import docs_service
        return docs_service.generate_mkdocs(
            workspace_path=args["workspace_path"],
            site_name=args["site_name"],
            pages=args["pages"],
        )

    else:
        return {"error": f"Unknown tool: {name}"}


async def main():
    server = _build_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
