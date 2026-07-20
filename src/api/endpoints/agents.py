"""
REST API — Agents endpoints.
Thin adapter over src.core.services.agent_service.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from src.core.services import agent_service
from src.core.security.auth import get_current_user, get_current_supervisor, UserIdentity

router = APIRouter()


class ExecuteAgentRequest(BaseModel):
    agent_name: str = Field(..., description="Name of the agent to execute")
    user_id: str = Field(..., description="User ID for tenant isolation")
    tenant_id: str = Field(..., description="Tenant ID for sandbox isolation")
    payload: dict = Field(default_factory=dict, description="Context payload for the agent")
    session_id: Optional[str] = Field(None, description="Optional session/job ID")


@router.get("/")
async def list_agents(user: UserIdentity = Depends(get_current_user)):
    """List all agents across projects."""
    agents = agent_service.list_agents()
    return {"agents": agents}


@router.get("/{agent_name}")
async def get_agent(agent_name: str, user: UserIdentity = Depends(get_current_user)):
    """Get a specific agent's manifest and metadata."""
    agent = agent_service.get_agent(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    return {"agent": agent}


@router.post("/execute")
async def execute_agent(req: ExecuteAgentRequest, user: UserIdentity = Depends(get_current_user)):
    """Trigger a LangGraph execution flow for the specified agent."""
    if user.user_id != req.user_id and "Supervisor" not in user.roles:
        raise HTTPException(
            status_code=403,
            detail="Authenticated user does not match the requested execution user_id or lack supervisory privileges."
        )

    agent = agent_service.get_agent(req.agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{req.agent_name}' not found")

    result = await agent_service.execute_agent(
        agent_name=req.agent_name,
        payload=req.payload,
        user_id=req.user_id,
        tenant_id=req.tenant_id,
        session_id=req.session_id,
    )
    return result


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str, user: UserIdentity = Depends(get_current_user)):
    """Check the status of an enqueued agent execution."""
    return await agent_service.get_execution_status(job_id)


class RewindCheckpointRequest(BaseModel):
    checkpoint_id: str = Field(..., description="UUIDv7 of the checkpoint to rewind to")


@router.post("/rewind")
async def rewind_checkpoint(req: RewindCheckpointRequest, user: UserIdentity = Depends(get_current_supervisor)):
    """Rewind a session to a specific UUIDv7 checkpoint ID."""
    try:
        return agent_service.rewind_checkpoint(req.checkpoint_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

