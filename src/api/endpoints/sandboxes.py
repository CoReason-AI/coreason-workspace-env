from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from src.api.endpoints.agents import get_current_identity
from src.core.services import sandbox_service

router = APIRouter()


class ProvisionSandboxRequest(BaseModel):
    project_id: str
    environment: str = "test"
    secrets: Optional[Dict[str, str]] = None
    connections: Optional[Dict[str, str]] = None
    mcp_servers: Optional[List[str]] = None


class ExecuteSandboxRequest(BaseModel):
    payload: Dict[str, Any]


@router.post("/provision")
async def provision_sandbox(req: ProvisionSandboxRequest, identity=Depends(get_current_identity)):
    """Provision a new sandboxed deployment environment with secrets & DB connections."""
    from src.core.services.rbac_service import rbac_service
    rbac_service.require_role(identity, "developer")

    record = sandbox_service.provision_sandbox(
        project_id=req.project_id,
        user_id=identity.user_id,
        tenant_id=identity.tenant_id,
        environment=req.environment,
        secrets=req.secrets,
        connections=req.connections,
        mcp_servers=req.mcp_servers,
    )
    return {"sandbox": record.model_dump()}


@router.get("/")
async def list_sandboxes(project_id: Optional[str] = None):
    """List all active sandboxed environments."""
    sandboxes = sandbox_service.list_sandboxes(project_id=project_id)
    return {"sandboxes": sandboxes}


@router.get("/{sandbox_id}")
async def get_sandbox(sandbox_id: str):
    """Get details of a specific sandbox environment."""
    sbx = sandbox_service.get_sandbox(sandbox_id)
    if not sbx:
        raise HTTPException(status_code=404, detail=f"Sandbox '{sandbox_id}' not found.")
    return {"sandbox": sbx}


@router.post("/{sandbox_id}/execute")
async def execute_in_sandbox(sandbox_id: str, req: ExecuteSandboxRequest, identity=Depends(get_current_identity)):
    """Execute a task/payload inside a provisioned sandbox environment."""
    res = sandbox_service.execute_in_sandbox(sandbox_id, req.payload)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res["message"])
    return res


@router.delete("/{sandbox_id}")
async def terminate_sandbox(sandbox_id: str, identity=Depends(get_current_identity)):
    """Terminate and clean up a provisioned sandbox environment."""
    from src.core.services.rbac_service import rbac_service
    rbac_service.require_role(identity, "developer")

    res = sandbox_service.terminate_sandbox(sandbox_id)
    if res.get("status") == "error":
        raise HTTPException(status_code=404, detail=res["message"])
    return res
