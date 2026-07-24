from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from src.api.endpoints.agents import get_current_identity
from src.core.services import catalog_service

router = APIRouter()


class RegisterCatalogEntryRequest(BaseModel):
    urn: str
    name: str
    description: str
    resource_type: str
    version: str = "1.0.0"
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    source_code: Optional[str] = None


class ImportCatalogModuleRequest(BaseModel):
    urn: str
    target_project_id: str


@router.get("/search")
async def search_catalog(
    query: Optional[str] = None,
    resource_type: Optional[str] = None,
    tags: Optional[str] = None,
):
    """Search the Project & Module Catalog (PEN 66197 Authority)."""
    parsed_tags = tags.split(",") if tags else None
    results = catalog_service.search_catalog(query=query, resource_type=resource_type, tags=parsed_tags)
    return {"results": results}


@router.get("/resolve/{urn:path}")
async def resolve_urn(urn: str):
    """Resolve an OID (urn:oid:1.3.6.1.4.1.66197:...) or Native URN (urn:coreason:...) to its metadata."""
    entry = catalog_service.resolve_urn(urn)
    if not entry:
        raise HTTPException(status_code=404, detail=f"URN '{urn}' not found in catalog.")
    return {"entry": entry}


@router.post("/register")
async def register_catalog_entry(req: RegisterCatalogEntryRequest, identity=Depends(get_current_identity)):
    """Register a new project or component under URN PEN 66197 authority."""
    from src.core.services.rbac_service import rbac_service
    rbac_service.require_role(identity, "developer")

    entry = catalog_service.register_entry(
        urn=req.urn,
        name=req.name,
        description=req.description,
        resource_type=req.resource_type,
        version=req.version,
        tags=req.tags,
        metadata=req.metadata,
        source_code=req.source_code,
    )
    return {"entry": entry.model_dump()}


@router.post("/import")
async def import_catalog_module(req: ImportCatalogModuleRequest, identity=Depends(get_current_identity)):
    """Import a cataloged project/agent module as a component into a project space."""
    res = catalog_service.import_module(req.urn, req.target_project_id)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res["message"])
    return res
