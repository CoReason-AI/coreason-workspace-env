"""
Portability Service — handles OCI artifact pushes and RO-Crate metadata.
"""
import os
import shutil
import uuid
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional

from rocrate.rocrate import ROCrate
from oras.client import OrasClient
from src.core.services.health_service import HealthService
from src.core.services.project_service import ProjectService

project_service = ProjectService()
health_service = HealthService()
from src.core.db import get_db_pool
import json
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_INIT_SQL = """
CREATE TABLE IF NOT EXISTS portability_jobs (
    job_id      TEXT PRIMARY KEY,
    project_id  TEXT,
    job_type    TEXT,
    status      TEXT,
    error       TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);
"""

class PortabilityService:
    """Service to handle industry-standard OCI and RO-Crate portability."""

    async def initialize(self):
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute(_INIT_SQL)

    async def _create_job(self, job_id: str, project_id: str, job_type: str, status: str):
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO portability_jobs (job_id, project_id, job_type, status) VALUES ($1, $2, $3, $4)",
                job_id, project_id, job_type, status
            )

    async def _update_job(self, job_id: str, status: str, error: str = "", project_id: str = None):
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            if project_id:
                await conn.execute(
                    "UPDATE portability_jobs SET status = $1, error = $2, project_id = $3, updated_at = NOW() WHERE job_id = $4",
                    status, error, project_id, job_id
                )
            else:
                await conn.execute(
                    "UPDATE portability_jobs SET status = $1, error = $2, updated_at = NOW() WHERE job_id = $3",
                    status, error, job_id
                )

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM portability_jobs WHERE job_id = $1", job_id)
            if not row:
                return {"status": "not_found"}
            return dict(row)

    async def export_to_oci(self, project_id: str, registry_url: str, skip_state: bool = False, skip_docker: bool = False) -> Dict[str, Any]:
        """
        Immediately returns a job_id and spawns a background export task.
        """
        job_id = str(uuid.uuid7())
        await self._create_job(job_id, project_id, "EXPORT", "ACCEPTED")
        
        # Spawn the background task
        asyncio.create_task(self._run_export_background(job_id, project_id, registry_url, skip_state, skip_docker))
        
        return {
            "status": "accepted",
            "job_id": job_id,
            "registry_url": registry_url
        }

    async def _run_export_background(self, job_id: str, project_id: str, registry_url: str, skip_state: bool, skip_docker: bool):
        await self._update_job(job_id, "RUNNING")
        import tempfile
        temp_dir = Path(tempfile.mkdtemp())
        
        logger.info(json.dumps({
            "event": "PortabilityExportStarted",
            "job_id": job_id,
            "project_id": project_id,
            "registry": registry_url,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }))

        try:
            # 1. Base Export (pg_dump, workspace.tar.gz, image.tar)
            export_result = await project_service.export_project(
                project_id, 
                str(temp_dir), 
                skip_state=skip_state, 
                skip_docker=skip_docker
            )
            if export_result.get("status") != "success":
                raise RuntimeError(f"Base export failed: {export_result}")

            # 2. Add RO-Crate Metadata
            project = await project_service.get_project(project_id)
            if not project:
                project = {}
            crate = ROCrate()
            crate.name = project.get("name", "Unknown Project")
            crate.description = project.get("description", "Exported CoReason Project")
            
            for filepath in export_result.get("files_written", []):
                crate.add_file(filepath)
                
            from src.core.services.health_service import HealthService
            current_version = HealthService().get_version().get("version", "unknown")
            crate.publisher = {"@id": "https://coreason.ai", "name": "CoReason Workspace Env"}
            crate.root_dataset["version"] = current_version
                
            crate.write(str(temp_dir))

            # 3. Push to OCI Registry
            logger.info(f"Pushing bundle to {registry_url}...")
            is_insecure = "localhost" in registry_url or "127.0.0.1" in registry_url or os.environ.get("ORAS_INSECURE", "").lower() == "true"
            client = OrasClient(insecure=is_insecure)
            
            if "ORAS_USER" in os.environ and "ORAS_PASS" in os.environ:
                client.login(
                    username=os.environ["ORAS_USER"], 
                    password=os.environ["ORAS_PASS"]
                )
                
            client.push(target=registry_url, files=[str(temp_dir)], disable_path_validation=True)

            logger.info(json.dumps({
                "event": "PortabilityExportCompleted",
                "job_id": job_id,
                "project_id": project_id,
                "registry": registry_url,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }))
            await self._update_job(job_id, "COMPLETED")

        except Exception as e:
            logger.error(f"Failed to push OCI artifact: {e}")
            await self._update_job(job_id, "FAILED", str(e))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


    async def import_from_oci(self, oci_uri: str, name: str, description: str = "", skip_state: bool = False, skip_docker: bool = False) -> Dict[str, Any]:
        """
        Immediately returns a job_id and spawns a background import task.
        """
        job_id = str(uuid.uuid7())
        # We don't have a project_id yet because it's an import, so we'll leave it blank for now
        await self._create_job(job_id, "", "IMPORT", "ACCEPTED")
        
        asyncio.create_task(self._run_import_background(job_id, oci_uri, name, description, skip_state, skip_docker))
        
        return {
            "status": "accepted",
            "job_id": job_id,
            "oci_uri": oci_uri
        }

    async def _run_import_background(self, job_id: str, oci_uri: str, name: str, description: str, skip_state: bool, skip_docker: bool):
        await self._update_job(job_id, "RUNNING")
        import tempfile
        temp_dir = Path(tempfile.mkdtemp())
        
        logger.info(json.dumps({
            "event": "PortabilityImportStarted",
            "job_id": job_id,
            "oci_uri": oci_uri,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }))

        try:
            # 1. Pull OCI Artifact
            logger.info(f"Pulling OCI artifact from {oci_uri}...")
            is_insecure = "localhost" in oci_uri or "127.0.0.1" in oci_uri or os.environ.get("ORAS_INSECURE", "").lower() == "true"
            client = OrasClient(insecure=is_insecure)
            
            if "ORAS_USER" in os.environ and "ORAS_PASS" in os.environ:
                client.login(
                    username=os.environ["ORAS_USER"], 
                    password=os.environ["ORAS_PASS"]
                )

            client.pull(target=oci_uri, outdir=str(temp_dir))
            
            # 2. Validate RO-Crate and Version
            crate_path = temp_dir / "ro-crate-metadata.json"
            if not crate_path.exists():
                logger.warning("No RO-Crate metadata found in the OCI artifact. Proceeding with raw import.")
            else:
                with open(crate_path, "r") as f:
                    crate_data = json.load(f)
                    
                export_version = crate_data.get("@graph", [{}])[0].get("version", "unknown")
                from src.core.services.health_service import HealthService
                local_version = HealthService().get_version().get("version", "unknown")
                
                if export_version != local_version:
                    logger.warning(
                        f"Version Mismatch Detected! Bundle was exported from v{export_version}, "
                        f"but local environment is v{local_version}. Proceeding optimistically..."
                    )
            
            # 3. Base Import
            project_id = str(uuid.uuid7())
            import_result = await project_service.import_project(
                project_id=project_id,
                import_path=str(temp_dir),
                name=name,
                description=description,
                config={},
                skip_state=skip_state,
                skip_docker=skip_docker
            )
            
            logger.info(json.dumps({
                "event": "PortabilityImportCompleted",
                "job_id": job_id,
                "project_id": import_result["project"]["id"],
                "oci_uri": oci_uri,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }))
            
            # Update the job with the newly created project ID and mark completed
            await self._update_job(job_id, "COMPLETED", project_id=import_result["project"]["id"])
            
        except Exception as e:
            logger.error(f"Failed to pull or import OCI artifact: {e}")
            await self._update_job(job_id, "FAILED", str(e))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

portability_service = PortabilityService()
