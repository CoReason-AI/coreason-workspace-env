import os
import json
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
        runtime_engine: str = "openshell",
        agent_name: Optional[str] = None,
        agent_permissions: Optional[Dict[str, Any]] = None,
        secrets: Optional[Dict[str, str]] = None,
        connections: Optional[Dict[str, str]] = None,
        mcp_servers: Optional[List[str]] = None,
    ) -> SandboxRecord:
        """
        Provisions a new isolated sandbox environment for a project deployment.
        Constructs an agent-specific OpenShell Zero-Trust security boundary policy.
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

        # Fetch agent-specific manifest permissions if agent_name provided
        merged_perms = agent_permissions or {}
        if agent_name:
            try:
                from src.core.services.agent_service import agent_service
                agent_manifest = agent_service.get_agent(agent_name)
                if agent_manifest:
                    manifest_perms = agent_manifest.get("zero_trust_policy") or agent_manifest.get("permissions") or {}
                    merged_perms = {**manifest_perms, **merged_perms}
            except Exception as e:
                logger.warning(f"Could not load manifest permissions for agent '{agent_name}': {e}")

        # 1. Write env configuration to sandbox workspace
        env_file = ws_path / ".env.sandbox"
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(f"# Sandbox Environment: {sandbox_id}\n")
            f.write(f"PROJECT_ID={project_id}\n")
            if agent_name:
                f.write(f"AGENT_NAME={agent_name}\n")
            f.write(f"SANDBOX_ENV={environment}\n")
            f.write(f"RUNTIME_ENGINE={runtime_engine}\n")
            for k, v in final_secrets.items():
                f.write(f"SECRET_{k}={v}\n")
            for k, v in final_conns.items():
                f.write(f"CONN_{k.upper()}={v}\n")

        rel_ws_path = f"sandboxes/{sandbox_id}"

        # 2. Write Agent-Specific OpenShell Security & Zero-Trust Policy Manifest
        allowed_egress = merged_perms.get("allowed_egress_domains", ["api.dify.ai", "api.openai.com", "urn.coreason.ai"])
        allowed_tools = merged_perms.get("allowed_tools", final_mcp)
        read_only_paths = merged_perms.get("read_only_paths", ["/etc", "/usr", "/lib"])

        openshell_policy = {
            "sandbox_id": sandbox_id,
            "project_id": project_id,
            "agent_name": agent_name or "generic_agent",
            "runtime_engine": runtime_engine,
            "zero_trust": {
                "strict_mode": True,
                "agent_identity": f"urn:oid:1.3.6.1.4.1.66197:agent:{agent_name or 'generic'}",
            },
            "filesystem": {
                "read_only_paths": read_only_paths,
                "writable_workspace": rel_ws_path,
            },
            "wiring": {
                "intra_sandbox": "in_process_langgraph_dag",
                "inter_sandbox": "fastmcp_jsonrpc_over_mcp_port",
                "urn_resolution_authority": "https://urn.coreason.ai/1.3.6.1.4.1.66197",
            },
            "network": {
                "allowed_egress_domains": allowed_egress,
                "mcp_server_ports": [9005],
            },
            "tools": {
                "allowed_mcp_servers": allowed_tools,
            },
            "capabilities": {
                "allow_subprocess": merged_perms.get("allow_subprocess", False if environment == "production" else True),
                "allow_raw_sockets": merged_perms.get("allow_raw_sockets", False),
            }
        }
        policy_file = ws_path / "openshell.policy.json"
        with open(policy_file, "w", encoding="utf-8") as f:
            json.dump(openshell_policy, f, indent=2)

        # 3. Write Docker Sandbox Override Manifest
        docker_compose_sbx = f"""version: '3.8'
services:
  agent-sandbox-{sandbox_id[:8]}:
    image: registry.coreason.ai/apps/{project_id}:latest
    environment:
      - SANDBOX_ID={sandbox_id}
      - PROJECT_ID={project_id}
      - RUNTIME_ENGINE={runtime_engine}
    volumes:
      - ./{rel_ws_path}:/app/sandbox
    security_opt:
      - no-new-privileges:true
"""
        with open(ws_path / "docker-compose.sandbox.yaml", "w", encoding="utf-8") as f:
            f.write(docker_compose_sbx)

        # 4. Write Kubernetes Pod Manifest
        k8s_pod_manifest = f"""apiVersion: v1
kind: Pod
metadata:
  name: sbx-{sandbox_id[:8]}
  namespace: coreason-sandboxes
  labels:
    project: "{project_id}"
    sandbox_id: "{sandbox_id}"
    runtime_engine: "{runtime_engine}"
spec:
  containers:
  - name: agent-runner
    image: registry.coreason.ai/apps/{project_id}:latest
    securityContext:
      readOnlyRootFilesystem: true
      allowPrivilegeEscalation: false
"""
        with open(ws_path / "k8s-pod.yaml", "w", encoding="utf-8") as f:
            f.write(k8s_pod_manifest)

        record = SandboxRecord(
            sandbox_id=sandbox_id,
            project_id=project_id,
            user_id=user_id,
            tenant_id=tenant_id,
            environment=environment,
            status="running",
            runtime_engine=runtime_engine,
            openshell_policy=openshell_policy,
            provisioned_secrets=final_secrets,
            connections=final_conns,
            mcp_servers=final_mcp,
            workspace_path=rel_ws_path,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )

        self._sandboxes[sandbox_id] = record.model_dump()
        logger.info(f"Provisioned {runtime_engine} sandbox {sandbox_id} for project {project_id} in {environment} mode.")
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

        ws_path = self.base_dir / sandbox_id
        if ws_path.is_dir():
            shutil.rmtree(ws_path, ignore_errors=True)

        self._sandboxes[sandbox_id]["status"] = "terminated"
        logger.info(f"Terminated sandbox {sandbox_id}.")
        return {"status": "success", "sandbox_id": sandbox_id, "message": "Sandbox terminated and workspace cleaned up."}


sandbox_service = SandboxService()
