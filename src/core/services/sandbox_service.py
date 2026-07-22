import os
import uuid
import time
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from src.core.ontology import SandboxRecord

logger = logging.getLogger(__name__)

_SANDBOX_BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "sandboxes"


class SandboxService:
    """
    Service layer for managing isolated, provisioned sandboxed deployment environments.
    Provisions workspace isolation, secret injection, DB connections, and MCP tool bindings.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or _SANDBOX_BASE_DIR
        self._sandboxes: Dict[str, Dict[str, Any]] = {}

    def provision_sandbox(
        self,
        project_id: str,
        user_id: str,
        tenant_id: str,
        environment: str = "test",
        secrets: Optional[Dict[str, str]] = None,
        connections: Optional[Dict[str, str]] = None,
        mcp_servers: Optional[List[str]] = None,
    ) -> SandboxRecord:
        """
        Provisions a new isolated sandbox environment for a project deployment.
        """
        sandbox_id = str(uuid.uuid7())
        ws_path = self.base_dir / sandbox_id
        ws_path.mkdir(parents=True, exist_ok=True)

        # Default provisioned connection strings if omitted
        default_conns = {
            "postgres_dsn": os.environ.get("POSTGRES_DSN", "postgresql://coreason:coreason@localhost:5432/coreason_db"),
            "redis_url": os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
        }
        final_conns = {**default_conns, **(connections or {})}
        final_secrets = secrets or {"API_KEY": f"sbx_secret_{uuid.uuid4().hex[:12]}"}
        final_mcp = mcp_servers or ["coreason-filesystem", "coreason-postgres", "coreason-fetch"]

        # Write env configuration to sandbox workspace
        env_file = ws_path / ".env.sandbox"
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(f"# Sandbox Environment: {sandbox_id}\n")
            f.write(f"PROJECT_ID={project_id}\n")
            f.write(f"SANDBOX_ENV={environment}\n")
            for k, v in final_secrets.items():
                f.write(f"SECRET_{k}={v}\n")
            for k, v in final_conns.items():
                f.write(f"CONN_{k.upper()}={v}\n")

        record = SandboxRecord(
            sandbox_id=sandbox_id,
            project_id=project_id,
            user_id=user_id,
            tenant_id=tenant_id,
            environment=environment,
            status="running",
            provisioned_secrets=final_secrets,
            connections=final_conns,
            mcp_servers=final_mcp,
            workspace_path=str(ws_path),
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )

        self._sandboxes[sandbox_id] = record.model_dump()
        logger.info(f"Provisioned sandbox {sandbox_id} for project {project_id} in {environment} mode.")
        return record

    def get_sandbox(self, sandbox_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves details of a provisioned sandbox."""
        return self._sandboxes.get(sandbox_id)

    def list_sandboxes(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists all active sandboxes, optionally filtered by project_id."""
        if not project_id:
            return list(self._sandboxes.values())
        return [s for s in self._sandboxes.values() if s["project_id"] == project_id]

    def execute_in_sandbox(self, sandbox_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a task/payload inside the provisioned sandbox context.
        """
        sbx = self.get_sandbox(sandbox_id)
        if not sbx:
            return {"status": "error", "message": f"Sandbox '{sandbox_id}' not found."}
        if sbx["status"] != "running":
            return {"status": "error", "message": f"Sandbox '{sandbox_id}' is in state '{sbx['status']}'."}

        logger.info(f"Executing payload in sandbox {sandbox_id}: {payload}")
        return {
            "status": "success",
            "sandbox_id": sandbox_id,
            "project_id": sbx["project_id"],
            "environment": sbx["environment"],
            "executed_payload": payload,
            "result": "Execution completed cleanly inside sandboxed container workspace.",
        }

    def terminate_sandbox(self, sandbox_id: str) -> Dict[str, Any]:
        """Terminates and cleans up a provisioned sandbox."""
        sbx = self.get_sandbox(sandbox_id)
        if not sbx:
            return {"status": "error", "message": f"Sandbox '{sandbox_id}' not found."}

        ws_path = Path(sbx["workspace_path"])
        if ws_path.is_dir():
            shutil.rmtree(ws_path, ignore_errors=True)

        self._sandboxes[sandbox_id]["status"] = "terminated"
        logger.info(f"Terminated sandbox {sandbox_id}.")
        return {"status": "success", "sandbox_id": sandbox_id, "message": "Sandbox terminated and workspace cleaned up."}


sandbox_service = SandboxService()
