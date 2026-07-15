"""
REST API — Documentation Service endpoints.
Thin adapter over src.core.services.docs_service.
"""
from typing import List, Dict, Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.core.services import docs_service

router = APIRouter()


class MkDocsPage(BaseModel):
    title: str
    filename: str
    content: str


class MkDocsConfig(BaseModel):
    site_name: str
    site_description: Optional[str] = "CoReason Auto-Generated Docs"
    theme: Optional[Dict[str, Any]] = Field(default_factory=lambda: {"name": "material"})
    nav: Optional[List[Dict[str, str]]] = None


class GenerateDocsRequest(BaseModel):
    workspace_path: str
    config: MkDocsConfig
    pages: List[MkDocsPage]


@router.post("/generate")
async def generate_mkdocs(request: GenerateDocsRequest):
    """Scaffolds an MkDocs workspace (mkdocs.yml and docs/ folder)."""
    pages = [{"title": p.title, "filename": p.filename, "content": p.content} for p in request.pages]
    result = docs_service.generate_mkdocs(
        workspace_path=request.workspace_path,
        site_name=request.config.site_name,
        pages=pages,
        site_description=request.config.site_description,
        theme=request.config.theme,
        nav=request.config.nav,
    )
    if result["status"] == "error":
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Docs generation error: {result['detail']}")
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Documentation generation failed due to a workspace or configuration error.")
    return result
