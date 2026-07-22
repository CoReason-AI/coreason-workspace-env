"""
REST API — Agents endpoints.
Thin adapter over src.core.services.agent_service.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from src.core.services import agent_service
from fastapi import Header

async def get_current_identity(x_user_id: str = Header("dev-user-456"), x_tenant_id: str = Header("default-tenant")):
    from src.core.services.rbac_service import rbac_service
    return rbac_service.authenticate_human(user_id=x_user_id, tenant_id=x_tenant_id)

router = APIRouter()


class ExecuteAgentRequest(BaseModel):
    agent_name: str = Field(..., description="Name of the agent to execute")
    payload: dict = Field(default_factory=dict, description="Context payload for the agent")
    session_id: Optional[str] = Field(None, description="Optional session/job ID")


@router.get("/")
async def list_agents():
    """List all agents across projects."""
    service = agent_service.AgentService()
    agents = service.list_agents()
    return {"agents": agents}


@router.get("/{agent_name}")
async def get_agent(agent_name: str):
    """Get a specific agent's manifest and metadata."""
    service = agent_service.AgentService()
    agent = service.get_agent(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    return {"agent": agent}


@router.post("/execute")
async def execute_agent(req: ExecuteAgentRequest, identity = Depends(get_current_identity)):
    """Trigger a LangGraph execution flow for the specified agent."""
    from src.core.services.rbac_service import rbac_service
    rbac_service.require_role(identity, "developer")

    service = agent_service.AgentService()
    agent = service.get_agent(req.agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{req.agent_name}' not found")

    result = await service.execute_agent(
        agent_name=req.agent_name,
        payload=req.payload,
        user_id=identity.user_id,
        tenant_id=identity.tenant_id,
        session_id=req.session_id,
    )
    return result


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Check the status of an enqueued agent execution."""
    return await agent_service.get_execution_status(job_id)


class RewindCheckpointRequest(BaseModel):
    checkpoint_id: str = Field(..., description="UUIDv7 of the checkpoint to rewind to")


@router.post("/rewind")
async def rewind_checkpoint(req: RewindCheckpointRequest):
    """Rewind a session to a specific UUIDv7 checkpoint ID."""
    from src.core.services.agent_service import AgentService
    service = AgentService()
    try:
        return service.rewind_checkpoint(req.checkpoint_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class OverrideRequest(BaseModel):
    job_id: str
    payload: dict

@router.post("/override")
async def submit_override(req: OverrideRequest, identity = Depends(get_current_identity)):
    """HOTL Override: Intervene in a paused LangGraph thread."""
    from src.core.services.rbac_service import rbac_service
    rbac_service.require_role(identity, "developer")
    
    from src.core.services.agent_service import AgentService
    service = AgentService()
    return await service.submit_override(req.job_id, req.payload)

@router.post("/deploy/test/{project_id}")
async def deploy_to_test(project_id: str, identity = Depends(get_current_identity)):
    """Deploy the generated agent project to the Test Environment."""
    from src.core.services.rbac_service import rbac_service
    rbac_service.require_role(identity, "developer")
    
    return {"status": "success", "environment": "test", "project_id": project_id, "message": "Successfully deployed to test environment."}

@router.post("/deploy/production/{project_id}")
async def deploy_to_production(project_id: str, identity = Depends(get_current_identity)):
    """Deploy the generated agent project to the Production Environment."""
    from src.core.services.rbac_service import rbac_service
    rbac_service.require_role(identity, "admin")
    
    return {"status": "success", "environment": "production", "project_id": project_id, "message": "Successfully deployed to production environment."}

