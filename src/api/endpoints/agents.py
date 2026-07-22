"""
REST API — Agents endpoints.
Thin adapter over src.core.services.agent_service.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from src.core.services import agent_service
from fastapi import Header

async def get_current_identity(
    x_user_id: str = Header("dev-user-456"), 
    x_tenant_id: str = Header("default-tenant"),
    x_user_roles: Optional[str] = Header(None)
):
    from src.core.services.rbac_service import rbac_service
    roles = [r.strip() for r in x_user_roles.split(",")] if x_user_roles else None
    return rbac_service.authenticate_human(user_id=x_user_id, tenant_id=x_tenant_id, provided_roles=roles)

router = APIRouter()


class ExecuteAgentRequest(BaseModel):
    agent_name: str = Field(..., description="Name of the agent to execute")
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
async def execute_agent(req: ExecuteAgentRequest, identity = Depends(get_current_identity)):
    """Trigger a LangGraph execution flow for the specified agent."""
    from src.core.services.rbac_service import rbac_service
    rbac_service.require_role(identity, "developer")

    agent = agent_service.get_agent(req.agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{req.agent_name}' not found")

    result = await agent_service.execute_agent(
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
    try:
        return agent_service.rewind_checkpoint(req.checkpoint_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class OverrideRequest(BaseModel):
    job_id: str
    agent_name: str
    payload: dict

@router.post("/override")
async def submit_override(req: OverrideRequest, identity = Depends(get_current_identity)):
    """HOTL Override: Intervene in a paused LangGraph thread."""
    from src.core.services.rbac_service import rbac_service
    rbac_service.require_role(identity, "developer")
    
    return await agent_service.submit_override(req.job_id, req.agent_name, req.payload)

@router.post("/deploy/test/{project_id}")
async def deploy_to_test(project_id: str, identity = Depends(get_current_identity)):
    """Deploy the generated agent project to the Test Environment."""
    from src.core.services.rbac_service import rbac_service
    rbac_service.require_role(identity, "developer")
    
    return await agent_service.deploy_to_test(project_id, identity.user_id, identity.tenant_id)

@router.post("/deploy/production/{project_id}")
async def deploy_to_production(project_id: str, identity = Depends(get_current_identity)):
    """Deploy the generated agent project to the Production Environment."""
    from src.core.services.rbac_service import rbac_service
    rbac_service.require_role(identity, "admin")
    
    return await agent_service.deploy_to_production(project_id, identity.user_id, identity.tenant_id)


@router.get("/traces/{job_id}")
async def get_execution_trace(job_id: str):
    """Retrieve full execution trace for meta-programming and observability."""
    from src.core.services import trace_service
    trace = trace_service.get_trace(job_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace for job '{job_id}' not found.")
    return {"trace": trace}


class EvaluateAgentRequest(BaseModel):
    agent_name: str
    test_cases: list[dict]


@router.post("/evaluate")
async def evaluate_agent(req: EvaluateAgentRequest, identity = Depends(get_current_identity)):
    """Run an agent-level unit and E2E evaluation suite against an agent."""
    from src.core.services.rbac_service import rbac_service
    rbac_service.require_role(identity, "developer")
    
    from src.core.testing.agent_harness import agent_test_harness, TestCaseSpec
    specs = [TestCaseSpec(**tc) for tc in req.test_cases]
    report = await agent_test_harness.run_evaluation(
        agent_name=req.agent_name,
        test_cases=specs,
        user_id=identity.user_id,
        tenant_id=identity.tenant_id
    )
    return report.model_dump()

