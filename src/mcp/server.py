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
import os
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from dotenv import load_dotenv

from src.core.services import health_service, agent_service
from src.core.services.deepagent_service import deepagent_service
from src.core.services.rbac_service import rbac_service

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware import Middleware
from starlette.responses import JSONResponse

load_dotenv()
logger = logging.getLogger(__name__)

class BearerAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        expected_token = os.environ.get("MCP_API_KEY")
        if not expected_token:
            return JSONResponse({"error": "Server is improperly configured (MCP_API_KEY missing)"}, status_code=500)
        
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
            
        token = auth_header.split(" ")[1]
        if token != expected_token:
            return JSONResponse({"error": "Forbidden"}, status_code=403)
            
        return await call_next(request)

mcp = FastMCP("coreason-platform")

@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """Check platform health — Postgres, Redis connectivity and version info."""
    return await health_service.check()

@mcp.tool()
async def get_version() -> Dict[str, Any]:
    """Get platform version info."""
    return health_service.get_version()

@mcp.tool()
async def list_agents() -> Dict[str, Any]:
    """List all agents in the factory with their metadata."""
    return {"agents": agent_service.list_agents()}

@mcp.tool()
async def get_agent(agent_name: str) -> Dict[str, Any]:
    """Get a specific agent's manifest and metadata."""
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
    identity = rbac_service.authenticate_human(user_id, tenant_id, provided_roles=roles)
    rbac_service.require_role(identity, "developer")
    
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
    return await deepagent_service.run_native_deepagent(
        agent_name=agent_name,
        payload=payload or {},
    )

@mcp.tool()
async def get_execution_status(job_id: str) -> Dict[str, Any]:
    """Check the status of an enqueued agent execution."""
    return await agent_service.get_execution_status(job_id)

@mcp.tool()
async def rewind_checkpoint(checkpoint_id: str) -> Dict[str, Any]:
    """Rewind a session to a specific UUIDv7 checkpoint ID."""
    return agent_service.rewind_checkpoint(checkpoint_id)

@mcp.tool()
async def submit_override(job_id: str, agent_name: str, payload: Dict[str, Any], user_id: str, tenant_id: str, roles: Optional[List[str]] = None) -> Dict[str, Any]:
    """HOTL Override: Intervene in a paused LangGraph thread by injecting a state payload."""
    identity = rbac_service.authenticate_human(user_id, tenant_id, provided_roles=roles)
    rbac_service.require_role(identity, "developer")
    
    return await agent_service.submit_override(job_id, agent_name, payload)

@mcp.tool()
async def deploy_to_test(project_id: str, user_id: str, tenant_id: str, roles: Optional[List[str]] = None) -> Dict[str, Any]:
    """Deploy the generated agent project to the Test Environment."""
    identity = rbac_service.authenticate_human(user_id, tenant_id, provided_roles=roles)
    rbac_service.require_role(identity, "developer")
    
    logger.info(f"User {user_id} deploying project {project_id} to TEST environment...")
    # In a real implementation, this would trigger the OCI push with an 'rc' or 'test' tag.
    return {"status": "success", "environment": "test", "project_id": project_id, "message": "Successfully deployed to test environment."}

@mcp.tool()
async def deploy_to_production(project_id: str, user_id: str, tenant_id: str, roles: Optional[List[str]] = None) -> Dict[str, Any]:
    """Deploy the generated agent project to the Production Environment."""
    identity = rbac_service.authenticate_human(user_id, tenant_id, provided_roles=roles)
    rbac_service.require_role(identity, "admin")
    
    logger.info(f"User {user_id} deploying project {project_id} to PRODUCTION environment...")
    return {"status": "success", "environment": "production", "project_id": project_id, "message": "Successfully deployed to production environment."}

@mcp.tool()
async def get_trace(job_id: str) -> Dict[str, Any]:
    """Retrieve full execution trace for meta-programming and observability."""
    from src.core.services import trace_service
    trace = trace_service.get_trace(job_id)
    return {"trace": trace} if trace else {"error": f"Trace for job '{job_id}' not found"}

@mcp.tool()
async def evaluate_agent(
    agent_name: str,
    test_cases: List[Dict[str, Any]],
    user_id: str,
    tenant_id: str,
    roles: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Run an agent-level unit and E2E evaluation suite against an agent."""
    identity = rbac_service.authenticate_human(user_id, tenant_id, provided_roles=roles)
    rbac_service.require_role(identity, "developer")
    
    from src.core.testing.agent_harness import agent_test_harness, TestCaseSpec
    specs = [TestCaseSpec(**tc) for tc in test_cases]
    report = await agent_test_harness.run_evaluation(
        agent_name=agent_name,
        test_cases=specs,
        user_id=user_id,
        tenant_id=tenant_id
    )
    return report.model_dump()

@mcp.tool()
async def list_skills(category: Optional[str] = None) -> Dict[str, Any]:
    """List all available skills in the registry."""
    from src.core.services import skill_service
    return {"skills": skill_service.list_skills(category=category)}

@mcp.tool()
async def provision_sandbox(
    project_id: str,
    user_id: str,
    tenant_id: str,
    environment: str = "test",
    secrets: Optional[Dict[str, str]] = None,
    connections: Optional[Dict[str, str]] = None,
    mcp_servers: Optional[List[str]] = None,
    roles: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Provision a new sandboxed deployment environment with secrets & DB connections."""
    identity = rbac_service.authenticate_human(user_id, tenant_id, provided_roles=roles)
    rbac_service.require_role(identity, "developer")
    
    from src.core.services import sandbox_service
    rec = sandbox_service.provision_sandbox(
        project_id=project_id,
        user_id=user_id,
        tenant_id=tenant_id,
        environment=environment,
        secrets=secrets,
        connections=connections,
        mcp_servers=mcp_servers,
    )
    return {"sandbox": rec.model_dump()}

@mcp.tool()
async def get_sandbox(sandbox_id: str) -> Dict[str, Any]:
    """Get details of a provisioned sandbox environment."""
    from src.core.services import sandbox_service
    sbx = sandbox_service.get_sandbox(sandbox_id)
    return {"sandbox": sbx} if sbx else {"error": f"Sandbox '{sandbox_id}' not found"}

@mcp.tool()
async def execute_in_sandbox(sandbox_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a task/payload inside a provisioned sandbox environment."""
    from src.core.services import sandbox_service
    return sandbox_service.execute_in_sandbox(sandbox_id, payload)

@mcp.tool()
async def search_catalog(
    query: Optional[str] = None,
    resource_type: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Search the Project & Module Catalog (PEN 66197 Authority)."""
    from src.core.services import catalog_service
    results = catalog_service.search_catalog(query=query, resource_type=resource_type, tags=tags)
    return {"results": results}

@mcp.tool()
async def resolve_urn(urn: str) -> Dict[str, Any]:
    """Resolve an OID (urn:oid:1.3.6.1.4.1.66197:...) or Native URN (urn:coreason:...) to its metadata."""
    from src.core.services import catalog_service
    entry = catalog_service.resolve_urn(urn)
    return {"entry": entry} if entry else {"error": f"URN '{urn}' not found in catalog"}

@mcp.tool()
async def register_catalog_entry(
    urn: str,
    name: str,
    description: str,
    resource_type: str,
    user_id: str,
    tenant_id: str,
    version: str = "1.0.0",
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    source_code: Optional[str] = None,
    roles: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Register a new project or component under URN PEN 66197 authority."""
    identity = rbac_service.authenticate_human(user_id, tenant_id, provided_roles=roles)
    rbac_service.require_role(identity, "developer")
    
    from src.core.services import catalog_service
    entry = catalog_service.register_entry(
        urn=urn,
        name=name,
        description=description,
        resource_type=resource_type,
        version=version,
        tags=tags,
        metadata=metadata,
        source_code=source_code,
    )
    return {"entry": entry.model_dump()}

@mcp.tool()
async def import_catalog_module(urn: str, target_project_id: str) -> Dict[str, Any]:
    """Import a cataloged project/agent module as a component into a project space."""
    from src.core.services import catalog_service
    return catalog_service.import_module(urn, target_project_id)

if __name__ == "__main__":
    import os
    import sys
    logging.basicConfig(level=logging.INFO)
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower()
    if transport == "sse":
        if not os.environ.get("MCP_API_KEY"):
            logger.error("FATAL: MCP_API_KEY environment variable is required for SSE transport to secure the endpoint.")
            sys.exit(1)
        
        logger.info("Starting MCP server with authenticated SSE transport for Dify integration...")
        mcp.run(transport="sse", middleware=[Middleware(BearerAuthMiddleware)])
    else:
        mcp.run()

def _build_server():
    return mcp
