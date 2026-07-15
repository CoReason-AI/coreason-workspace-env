"""
CoReason Platform MCP Server — exposes all platform operations as MCP tools.
Enables upstream AI agents, IDEs, and orchestrators to control the platform natively.

All tools delegate to src.core.services (same shared business logic as API/CLI/SDK).

Usage:
    python -m src.mcp.server
"""
import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

mcp = FastMCP("coreason-platform")


@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """Check platform health — Postgres, Redis connectivity and version info."""
    from src.core.services import health_service
    return await health_service.check()


@mcp.tool()
async def get_version() -> Dict[str, Any]:
    """Get platform version info."""
    from src.core.services import health_service
    return health_service.get_version()


@mcp.tool()
async def list_projects() -> Dict[str, Any]:
    """List all projects in the workspace."""
    from src.core.services import project_service
    return {"projects": await project_service.list_projects()}


@mcp.tool()
async def create_project(name: str, description: str = "") -> Dict[str, Any]:
    """Create a new project."""
    from src.core.services import project_service
    project = await project_service.create_project(
        project_id=str(uuid.uuid7()),
        name=name,
        description=description,
    )
    return {"status": "created", "project": project}


@mcp.tool()
async def get_project(project_id: str) -> Dict[str, Any]:
    """Fetch a single project by ID."""
    from src.core.services import project_service
    project = await project_service.get_project(project_id)
    return {"project": project} if project else {"error": "Not found"}


@mcp.tool()
async def delete_project(project_id: str) -> Dict[str, Any]:
    """Delete a project by ID."""
    from src.core.services import project_service
    deleted = await project_service.delete_project(project_id)
    return {"status": "deleted"} if deleted else {"error": "Not found"}


@mcp.tool()
async def export_project(project_id: str, output_path: str) -> Dict[str, Any]:
    """Export a project for air-gapped transfer."""
    from src.core.services import project_service
    return await project_service.export_project(project_id, output_path)


@mcp.tool()
async def list_agents() -> Dict[str, Any]:
    """List all agents in the factory with their metadata."""
    from src.core.services import agent_service
    return {"agents": agent_service.list_agents()}


@mcp.tool()
async def get_agent(agent_name: str) -> Dict[str, Any]:
    """Get a specific agent's manifest and metadata."""
    from src.core.services import agent_service
    agent = agent_service.get_agent(agent_name)
    return {"agent": agent} if agent else {"error": "Not found"}


@mcp.tool()
async def execute_agent(
    agent_name: str,
    user_id: str,
    tenant_id: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Trigger a LangGraph execution flow for a specified agent."""
    from src.core.services import agent_service
    return await agent_service.execute_agent(
        agent_name=agent_name,
        payload=payload or {},
        user_id=user_id,
        tenant_id=tenant_id,
    )


@mcp.tool()
async def get_execution_status(job_id: str) -> Dict[str, Any]:
    """Check the status of an enqueued agent execution."""
    from src.core.services import agent_service
    return agent_service.get_execution_status(job_id)


@mcp.tool()
async def list_mcp_servers() -> Dict[str, Any]:
    """List connected MCP servers and their tools."""
    from src.core.services import mcp_tool_service
    return {"servers": mcp_tool_service.list_servers()}


@mcp.tool()
async def execute_mcp_tool(
    server_name: str,
    tool_name: str,
    arguments: Optional[Dict[str, Any]] = None,
    session_id: str = "mcp-session",
) -> Dict[str, Any]:
    """Execute a tool on a connected MCP server."""
    from src.core.services import mcp_tool_service
    return await mcp_tool_service.execute_tool(
        server_name=server_name,
        tool_name=tool_name,
        arguments=arguments or {},
        session_id=session_id,
    )


@mcp.tool()
async def generate_docs(
    workspace_path: str,
    site_name: str,
    pages: List[Dict[str, str]],
) -> Dict[str, Any]:
    """Generate an MkDocs scaffold with config and markdown pages."""
    from src.core.services import docs_service
    return docs_service.generate_mkdocs(
        workspace_path=workspace_path,
        site_name=site_name,
        pages=pages,
    )


@mcp.tool()
async def rewind_checkpoint(checkpoint_id: str) -> Dict[str, Any]:
    """Rewind a session to a specific UUIDv7 checkpoint ID."""
    from src.core.services import agent_service
    return agent_service.rewind_checkpoint(checkpoint_id)


@mcp.tool()
async def trigger_factory_build(user_id: str, session_id: str, intent: str) -> Dict[str, Any]:
    """Trigger a factory build for a new agent platform."""
    from src.core.services.orchestration_service import OrchestrationService
    orch = OrchestrationService()
    return await orch.run_factory_graph(user_id, session_id, intent)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # fastmcp handles stdio transport mapping automatically when run
    mcp.run()
