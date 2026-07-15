"""
REST API — Projects endpoints.
Thin adapter over src.core.services.project_service.
"""
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.core.services import project_service

router = APIRouter()


class CreateProjectRequest(BaseModel):
    name: str = Field(..., description="Unique project name")
    description: str = Field("", description="Project description")
    config: Optional[dict] = Field(None, description="Project configuration")


@router.get("/")
async def list_projects():
    """List all projects in the workspace."""
    projects = await project_service.list_projects()
    return {"projects": projects}


@router.post("/", status_code=201)
async def create_project(req: CreateProjectRequest):
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
async def get_project(project_id: str):
    """Fetch a single project by ID."""
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    return {"project": project}


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """Delete a project by ID."""
    deleted = await project_service.delete_project(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    return {"status": "deleted", "project_id": project_id}


@router.post("/{project_id}/export")
async def export_project(project_id: str, output_path: str):
    """Export a project for air-gapped transfer."""
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    result = await project_service.export_project(project_id, output_path)
    return result
