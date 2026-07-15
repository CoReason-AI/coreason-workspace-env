"""
Project Service — CRUD operations for projects.
"""
import json
import logging
import os
import subprocess
import tarfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from src.core.db import get_db_pool

logger = logging.getLogger(__name__)

# SQL for bootstrapping the projects table
_INIT_SQL = """
CREATE TABLE IF NOT EXISTS projects (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    description TEXT DEFAULT '',
    config      JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);
"""


class ProjectService:
    """
    Manages projects — CRUD, listing, and air-gapped export.
    All surfaces (API, CLI, MCP, SDK) delegate here.
    """



    async def initialize(self):
        """Bootstrap the projects table if it doesn't exist."""
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute(_INIT_SQL)
        logger.info("Projects table initialized.")

    async def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects."""
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM projects ORDER BY created_at DESC")
            return [dict(r) for r in rows]

    async def create_project(self, project_id: str, name: str,
                             description: str = "",
                             config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new project."""
        pool = await get_db_pool()
        cfg = json.dumps(config or {})
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO projects (id, name, description, config)
                VALUES ($1, $2, $3, $4::jsonb)
                RETURNING *
                """,
                project_id, name, description, cfg,
            )
            return dict(row)

    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single project by ID."""
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM projects WHERE id = $1", project_id)
            return dict(row) if row else None

    async def delete_project(self, project_id: str) -> bool:
        """Delete a project by ID."""
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            result = await conn.execute("DELETE FROM projects WHERE id = $1", project_id)
            return result == "DELETE 1"

    async def export_project(self, project_path: str, output_path: str) -> Dict[str, Any]:
        """
        Exports a project for full air-gapped portability.
        Bundles: Git workspace + Postgres pg_dump + Docker image.
        """
        from src.core.config import settings

        export_dir = Path(output_path)
        export_dir.mkdir(parents=True, exist_ok=True)

        files_written = []

        # 1. Export Postgres LangGraph State (pg_dump)
        logger.info("Snapshotting LangGraph Postgres Checkpointer State...")
        pg_dump_path = str(export_dir / "langgraph_state.dump")
        pg_dump_cmd = [
            "pg_dump",
            "-U", settings.POSTGRES_USER,
            "-h", settings.POSTGRES_HOST,
            "-p", str(settings.POSTGRES_PORT),
            "-F", "c",
            "-f", pg_dump_path,
            settings.POSTGRES_DB,
        ]
        env = os.environ.copy()
        env["PGPASSWORD"] = settings.POSTGRES_PASSWORD
        try:
            subprocess.run(pg_dump_cmd, env=env, check=True, capture_output=True)
            files_written.append(pg_dump_path)
        except Exception as e:
            logger.warning(f"pg_dump failed (is Postgres accessible?): {e}")

        # 2. Package the Git VFS Workspace
        logger.info("Packaging True Git VFS Workspace...")
        workspace_tar = str(export_dir / "workspace.tar.gz")
        with tarfile.open(workspace_tar, "w:gz") as tar:
            tar.add(project_path, arcname=os.path.basename(project_path))
        files_written.append(workspace_tar)

        # 3. Export Docker Image
        project_name = os.path.basename(project_path).lower()
        image_name = f"coreason/{project_name}:latest"
        docker_tar = str(export_dir / "image.tar")
        try:
            subprocess.run(
                ["docker", "save", "-o", docker_tar, image_name],
                check=True,
                capture_output=True,
            )
            files_written.append(docker_tar)
        except Exception as e:
            logger.warning(f"Docker export failed (is Docker running?): {e}")

        return {
            "status": "success",
            "export_path": str(export_dir),
            "files_written": files_written,
        }
