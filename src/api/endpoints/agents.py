"""
REST API — Agents endpoints.
Thin adapter over src.core.services.agent_service.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.core.services import agent_service

router = APIRouter()


class ExecuteAgentRequest(BaseModel):
    agent_name: str = Field(..., description="Name of the agent to execute")
    user_id: str = Field(..., description="User ID for tenant isolation")
    tenant_id: str = Field(..., description="Tenant ID for sandbox isolation")
    payload: dict = Field(default_factory=dict, description="Context payload for the agent")
    session_id: Optional[str] = Field(None, description="Optional session/job ID")


@router.get("/")
async def list_agents():
    """List all agents across projects."""
    agents = agent_service.list_agents()
    return {"agents": agents}


@router.get("/{agent_name}")
async def get_agent(agent_name: str):
    """Get a specific agent's manifest and metadata."""
    agent = agent_service.get_agent(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    return {"agent": agent}


@router.post("/execute")
async def execute_agent(req: ExecuteAgentRequest):
    """Trigger a LangGraph execution flow for the specified agent."""
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
async def get_job_status(job_id: str):
    """Check the status of an enqueued agent execution."""
    return agent_service.get_execution_status(job_id)
