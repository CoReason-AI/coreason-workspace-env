"""
REST API — Projects endpoints.
Thin adapter over src.core.services.project_service.
"""
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from src.core.adapters.dify_adapter import DifyAdapter
import os

def get_dify_adapter():
    # In a real app, API keys come from config/vault
    from src.core.adapters.dify_adapter import DifyAdapter
    # Implicitly uses settings.DIFY_API_KEY
    adapter = DifyAdapter()
    return adapter

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
async def list_projects():
    """List all projects in the workspace, proxied to Dify Workspaces."""
    adapter = get_dify_adapter()
    try:
        info = await adapter.get_workspace_info()
        return {"projects": [info]}
    except Exception as e:
        return {"projects": []}
    finally:
        await adapter.close()


@router.post("/", status_code=201)
async def create_project(req: CreateProjectRequest):
    adapter = get_dify_adapter()
    try:
        res = await adapter.create_workspace(req.name, req.description)
        return {"status": "created", "project": res}
    finally:
        await adapter.close()


@router.get("/{project_id}")
async def get_project(project_id: str):
    """Fetch a single project by ID (proxied to Dify)."""
    adapter = get_dify_adapter()
    try:
        res = await adapter.get_workspace_info()
        return {"project": res}
    finally:
        await adapter.close()


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """Delete a project by ID (proxied to Dify)."""
    adapter = get_dify_adapter()
    try:
        await adapter.delete_workspace(project_id)
        return {"status": "deleted", "project_id": project_id}
    finally:
        await adapter.close()


@router.post("/{project_id}/export")
async def export_project(project_id: str, output_path: str, skip_state: bool = False, skip_docker: bool = False):
    """Export a project for air-gapped transfer (proxied to Dify App Export)."""
    import json
    adapter = get_dify_adapter()
    try:
        res = await adapter.export_app(project_id)
        with open(output_path, "w") as f:
            json.dump(res, f)
        return {"status": "exported", "path": output_path}
    finally:
        await adapter.close()

@router.post("/import")
async def import_project(req: ImportProjectRequest, skip_state: bool = False, skip_docker: bool = False):
    """Import an air-gapped project (proxied to Dify App Import)."""
    import json
    adapter = get_dify_adapter()
    try:
        with open(req.import_path, "r") as f:
            data = json.load(f)
        res = await adapter.import_app(data)
        return {"status": "imported", "project": res}
    finally:
        await adapter.close()


