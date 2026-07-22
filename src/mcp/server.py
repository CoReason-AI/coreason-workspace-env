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
    """List all projects in the workspace (proxied to Dify)."""
    import os
    from src.core.adapters.dify_adapter import DifyAdapter
    # Implicitly uses settings.DIFY_API_KEY
    adapter = DifyAdapter()
    try:
        res = await adapter.get_workspace_info()
        return {"projects": [res]}
    except Exception:
        return {"projects": []}
    finally:
        await adapter.close()

@mcp.tool()
async def export_project(project_id: str, output_path: str, skip_state: bool = False, skip_docker: bool = False) -> Dict[str, Any]:
    """Export a project for air-gapped transfer (proxied to Dify)."""
    import os
    import json
    from src.core.adapters.dify_adapter import DifyAdapter
    # Implicitly uses settings.DIFY_API_KEY
    adapter = DifyAdapter()
    try:
        res = await adapter.export_app(project_id)
        with open(output_path, "w") as f:
            json.dump(res, f)
        return {"status": "exported", "path": output_path}
    finally:
        await adapter.close()

@mcp.tool()
async def import_project(name: str, import_path: str, description: str = "", skip_state: bool = False, skip_docker: bool = False) -> Dict[str, Any]:
    """Import a project from an air-gapped export bundle (proxied to Dify)."""
    import os
    import json
    from src.core.adapters.dify_adapter import DifyAdapter
    # Implicitly uses settings.DIFY_API_KEY
    adapter = DifyAdapter()
    try:
        with open(import_path, "r") as f:
            data = json.load(f)
        res = await adapter.import_app(data)
        return {"status": "imported", "project": res}
    finally:
        await adapter.close()


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
async def trigger_factory_build(user_id: str, session_id: str, intent: str) -> Dict[str, Any]:
    """Trigger a factory build for a new agent platform."""
    from src.core.services.agent_service import AgentService
    agent_service = AgentService()
    return await agent_service.execute_agent("factory_ceo", {"intent": intent}, user_id, "cli-tenant", session_id)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # fastmcp handles stdio transport mapping automatically when run
    mcp.run()

def _build_server():
    return mcp
