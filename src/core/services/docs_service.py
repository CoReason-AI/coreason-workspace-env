"""
Docs Service — MkDocs workspace generation.
Extracted from src/api/endpoints/docs.py to enable parity across surfaces.
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import yaml

logger = logging.getLogger(__name__)


class DocsService:
    """
    Generates MkDocs scaffolds (mkdocs.yml + docs/ pages).
    All surfaces (API, CLI, MCP, SDK) delegate here.
    """

    def generate_mkdocs(
        self,
        workspace_path: str,
        site_name: str,
        pages: List[Dict[str, str]],
        site_description: str = "CoReason Auto-Generated Docs",
        theme: Optional[Dict[str, Any]] = None,
        nav: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Scaffolds an MkDocs workspace with config and markdown pages.

        Args:
            workspace_path: Absolute path to create the MkDocs workspace.
            site_name: MkDocs site_name field.
            pages: List of dicts with 'title', 'filename', 'content' keys.
            site_description: MkDocs site_description.
            theme: MkDocs theme config. Defaults to Material.
            nav: Explicit nav structure. Auto-generated from pages if omitted.

        Returns:
            Structured result with status and files written.
        """
        from src.core.security.path_validation import validate_safe_path, WORKSPACE_ROOT
        try:
            workspace = validate_safe_path(workspace_path, base_dir=WORKSPACE_ROOT / "projects")
        except ValueError as e:
            return {"status": "error", "detail": str(e)}

        workspace.mkdir(parents=True, exist_ok=True)
        docs_dir = workspace / "docs"
        docs_dir.mkdir(exist_ok=True)

        # Build mkdocs.yml config
        mkdocs_config = {
            "site_name": site_name,
            "site_description": site_description,
            "theme": theme or {"name": "material"},
        }

        if nav:
            mkdocs_config["nav"] = nav
        else:
            mkdocs_config["nav"] = [{p["title"]: p["filename"]} for p in pages]

        mkdocs_yml = workspace / "mkdocs.yml"
        with open(mkdocs_yml, "w", encoding="utf-8") as f:
            yaml.dump(mkdocs_config, f, default_flow_style=False, sort_keys=False)

        # Write markdown pages
        written_files = [str(mkdocs_yml)]
        for page in pages:
            page_path = docs_dir / page["filename"]
            page_path.parent.mkdir(parents=True, exist_ok=True)
            page_path.write_text(page["content"], encoding="utf-8")
            written_files.append(str(page_path))

        return {
            "status": "success",
            "message": f"Generated MkDocs scaffold for '{site_name}'",
            "workspace": str(workspace),
            "files_written": written_files,
        }
