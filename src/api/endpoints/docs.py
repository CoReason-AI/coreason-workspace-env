import os
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

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
    """
    Scaffolds an MkDocs workspace (mkdocs.yml and docs/ folder).
    """
    workspace = Path(request.workspace_path)
    
    # 1. Validate Workspace
    if not workspace.is_absolute():
        raise HTTPException(status_code=400, detail="workspace_path must be absolute")
        
    try:
        workspace.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not create workspace directory: {str(e)}")

    docs_dir = workspace / "docs"
    docs_dir.mkdir(exist_ok=True)

    # 2. Generate mkdocs.yml
    mkdocs_config = {
        "site_name": request.config.site_name,
        "site_description": request.config.site_description,
        "theme": request.config.theme,
    }
    
    # If nav is explicitly provided, use it. Otherwise auto-generate from pages.
    if request.config.nav:
        mkdocs_config["nav"] = request.config.nav
    else:
        nav = []
        for page in request.pages:
            nav.append({page.title: page.filename})
        mkdocs_config["nav"] = nav

    mkdocs_yml_path = workspace / "mkdocs.yml"
    try:
        with open(mkdocs_yml_path, "w", encoding="utf-8") as f:
            yaml.dump(mkdocs_config, f, default_flow_style=False, sort_keys=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write mkdocs.yml: {str(e)}")

    # 3. Generate Markdown Pages
    written_files = []
    for page in request.pages:
        page_path = docs_dir / page.filename
        
        # Ensure subdirectories inside docs/ are created if filename has slashes
        page_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(page_path, "w", encoding="utf-8") as f:
                f.write(page.content)
            written_files.append(str(page_path))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to write {page.filename}: {str(e)}")

    return {
        "status": "success",
        "message": f"Successfully generated MkDocs scaffold for {request.config.site_name}",
        "workspace": str(workspace),
        "files_written": written_files
    }
