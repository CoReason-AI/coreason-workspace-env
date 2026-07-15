"""
REST API — Projects endpoints.
Thin adapter over src.core.services.project_service.
"""
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from src.core.services import project_service
from src.core.security.auth import get_current_user, UserIdentity

router = APIRouter()


class CreateProjectRequest(BaseModel):
    name: str = Field(..., description="Unique project name")
    description: str = Field("", description="Project description")
    config: Optional[dict] = Field(None, description="Project configuration")

class ImportProjectRequest(BaseModel):
    name: str = Field(..., description="Unique project name")
    import_path: str = Field(..., description="Path to the imported bundle")
    description: str = Field("", description="Project description")
    config: Optional[dict] = Field(None, description="Project configuration")

class PushProjectRequest(BaseModel):
    registry_url: str = Field(..., description="Target OCI registry URL")

class PullProjectRequest(BaseModel):
    oci_uri: str = Field(..., description="Source OCI registry URL")
    name: str = Field(..., description="Unique project name")
    description: str = Field("", description="Project description")


@router.get("/")
async def list_projects(user: UserIdentity = Depends(get_current_user)):
    """List all projects in the workspace."""
    projects = await project_service.list_projects()
    return {"projects": projects}


@router.post("/", status_code=201)
async def create_project(req: CreateProjectRequest, user: UserIdentity = Depends(get_current_user)):
    """Create a new project."""
    project_id = str(uuid.uuid7())
    try:
        project = await project_service.create_project(
            project_id=project_id,
            name=req.name,
            description=req.description,
            config=req.config,
        )
        return {"status": "created", "project": project}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project_id}")
async def get_project(project_id: str, user: UserIdentity = Depends(get_current_user)):
    """Fetch a single project by ID."""
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    return {"project": project}


@router.delete("/{project_id}")
async def delete_project(project_id: str, user: UserIdentity = Depends(get_current_user)):
    """Delete a project by ID."""
    deleted = await project_service.delete_project(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    return {"status": "deleted", "project_id": project_id}


@router.post("/{project_id}/export")
async def export_project(project_id: str, output_path: str, skip_state: bool = False, skip_docker: bool = False, user: UserIdentity = Depends(get_current_user)):
    """Export a project for air-gapped transfer."""
    try:
        from src.core.services import project_service
        result = await project_service.export_project(
            project_id, 
            output_path, 
            skip_state=skip_state, 
            skip_docker=skip_docker
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
