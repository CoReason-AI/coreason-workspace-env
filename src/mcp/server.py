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
    roles: Optional[List[str]] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Trigger a LangGraph execution flow for a specified agent."""
    from src.core.services.rbac_service import rbac_service
    identity = rbac_service.authenticate_human(user_id, tenant_id, provided_roles=roles)
    rbac_service.require_role(identity, "developer")
    
    from src.core.services import agent_service
    return await agent_service.execute_agent(
        agent_name=agent_name,
        payload=payload or {},
        user_id=user_id,
        tenant_id=tenant_id,
    )

@mcp.tool()
async def run_native_deepagent(
    agent_name: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute a local native deepagent (v0.6.0+) dynamically."""
    from src.core.services.deepagent_service import deepagent_service
    return await deepagent_service.run_native_deepagent(
        agent_name=agent_name,
        payload=payload or {},
    )

@mcp.tool()
async def get_execution_status(job_id: str) -> Dict[str, Any]:
    """Check the status of an enqueued agent execution."""
    from src.core.services import agent_service
    return await agent_service.get_execution_status(job_id)

@mcp.tool()
async def rewind_checkpoint(checkpoint_id: str) -> Dict[str, Any]:
    """Rewind a session to a specific UUIDv7 checkpoint ID."""
    from src.core.services import agent_service
    return agent_service.rewind_checkpoint(checkpoint_id)

@mcp.tool()
async def submit_override(job_id: str, agent_name: str, payload: Dict[str, Any], user_id: str, tenant_id: str, roles: Optional[List[str]] = None) -> Dict[str, Any]:
    """HOTL Override: Intervene in a paused LangGraph thread by injecting a state payload."""
    from src.core.services.rbac_service import rbac_service
    identity = rbac_service.authenticate_human(user_id, tenant_id, provided_roles=roles)
    rbac_service.require_role(identity, "developer")
    
    from src.core.services import agent_service
    service = agent_service.AgentService()
    return await service.submit_override(job_id, agent_name, payload)

@mcp.tool()
async def deploy_to_test(project_id: str, user_id: str, tenant_id: str, roles: Optional[List[str]] = None) -> Dict[str, Any]:
    """Deploy the generated agent project to the Test Environment."""
    from src.core.services.rbac_service import rbac_service
    identity = rbac_service.authenticate_human(user_id, tenant_id, provided_roles=roles)
    rbac_service.require_role(identity, "developer")
    
    logger.info(f"User {user_id} deploying project {project_id} to TEST environment...")
    # In a real implementation, this would trigger the OCI push with an 'rc' or 'test' tag.
    return {"status": "success", "environment": "test", "project_id": project_id, "message": "Successfully deployed to test environment."}

@mcp.tool()
async def deploy_to_production(project_id: str, user_id: str, tenant_id: str, roles: Optional[List[str]] = None) -> Dict[str, Any]:
    """Deploy the generated agent project to the Production Environment."""
    from src.core.services.rbac_service import rbac_service
    identity = rbac_service.authenticate_human(user_id, tenant_id, provided_roles=roles)
    rbac_service.require_role(identity, "admin")
    
    logger.info(f"User {user_id} deploying project {project_id} to PRODUCTION environment...")
    # In a real implementation, this would trigger the OCI push with a 'latest' or 'prod' tag.
    return {"status": "success", "environment": "production", "project_id": project_id, "message": "Successfully deployed to production environment."}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    mcp.run()

def _build_server():
    return mcp
