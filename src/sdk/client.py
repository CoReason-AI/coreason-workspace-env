"""
CoReason Python SDK Client — in-process access to all platform capabilities.
Delegates directly to src.core.services (no HTTP, no serialization overhead).

Usage:
    from src.sdk import CoReasonClient

    client = CoReasonClient()

    # Synchronous operations
    agents = client.agents.list()
    agent = client.agents.get("factory_ceo")

    # Async operations
    health = await client.health()
    projects = await client.projects.list()
    result = await client.agents.execute("yaml_compiler", payload={...}, user_id="u1", tenant_id="t1")
"""
import uuid
import json
from typing import Dict, Any, List, Optional


class _ProjectsNamespace:
    """SDK namespace for project operations."""

    def __init__(self):
        from src.core.services import project_service
        self._svc = project_service

    async def list(self) -> List[Dict[str, Any]]:
        """List all projects."""
        return await self._svc.list_projects()

    async def create(self, name: str, description: str = "",
                     config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new project."""
        return await self._svc.create_project(
            project_id=str(uuid.uuid7()),
            name=name,
            description=description,
            config=config,
        )

    async def get(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get a project by ID."""
        return await self._svc.get_project(project_id)

    async def delete(self, project_id: str) -> bool:
        """Delete a project by ID."""
        return await self._svc.delete_project(project_id)

    async def export(self, project_path: str, output_path: str, skip_state: bool = False, skip_docker: bool = False) -> Dict[str, Any]:
        """Export a project for air-gapped transfer."""
        return await self._svc.export_project(project_path, output_path, skip_state=skip_state, skip_docker=skip_docker)

    async def import_bundle(self, import_path: str, name: str, description: str = "",
                            config: Optional[Dict[str, Any]] = None, skip_state: bool = False, skip_docker: bool = False) -> Dict[str, Any]:
        """Import a project from an air-gapped export bundle."""
        return await self._svc.import_project(
            project_id=str(uuid.uuid7()),
            import_path=import_path,
            name=name,
            description=description,
            config=config,
            skip_state=skip_state,
            skip_docker=skip_docker
        )

    async def get_portability_job(self, job_id: str) -> Dict[str, Any]:
        from src.core.services.portability_service import portability_service
        return await portability_service.get_job_status(job_id)

    async def push_bundle(self, project_id: str, registry_url: str, skip_state: bool = False, skip_docker: bool = False) -> Dict[str, Any]:
        """Push a project to an OCI registry (Industry Standard) and block until completion."""
        import asyncio
        from src.core.services.portability_service import portability_service
        res = await portability_service.export_to_oci(project_id, registry_url, skip_state=skip_state, skip_docker=skip_docker)
        job_id = res["job_id"]
        
        while True:
            status = await self.get_portability_job(job_id)
            if status.get("status") == "COMPLETED":
                return {"status": "success", "job_id": job_id, "registry_url": registry_url}
            elif status.get("status") == "FAILED":
                raise RuntimeError(f"OCI Push Failed: {status.get('error')}")
            await asyncio.sleep(1)

    async def pull_bundle(self, oci_uri: str, name: str, description: str = "", skip_state: bool = False, skip_docker: bool = False) -> Dict[str, Any]:
        """Pull a project from an OCI registry (Industry Standard) and block until completion."""
        import asyncio
        from src.core.services.portability_service import portability_service
        res = await portability_service.import_from_oci(oci_uri, name, description, skip_state=skip_state, skip_docker=skip_docker)
        job_id = res["job_id"]
        
        while True:
            status = await self.get_portability_job(job_id)
            if status.get("status") == "COMPLETED":
                return {"status": "success", "job_id": job_id, "project_id": status.get("project_id"), "oci_uri": oci_uri}
            elif status.get("status") == "FAILED":
                raise RuntimeError(f"OCI Pull Failed: {status.get('error')}")
            await asyncio.sleep(1)

class _AgentsNamespace:
    """SDK namespace for agent operations."""

    def __init__(self):
        from src.core.services import agent_service
        self._svc = agent_service

    def list(self) -> List[Dict[str, Any]]:
        """List all agents (synchronous — reads YAML from disk)."""
        return self._svc.list_agents()

    def get(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific agent's manifest (synchronous)."""
        return self._svc.get_agent(agent_name)

    async def execute(
        self,
        agent_name: str,
        payload: Dict[str, Any] = None,
        user_id: str = "sdk-user",
        tenant_id: str = "sdk-tenant",
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Enqueue an agent execution."""
        return await self._svc.execute_agent(
            agent_name=agent_name,
            payload=payload or {},
            user_id=user_id,
            tenant_id=tenant_id,
            session_id=session_id,
        )

    def get_status(self, job_id: str) -> Dict[str, Any]:
        """Check the status of an enqueued job."""
        return self._svc.get_execution_status(job_id)

    def rewind_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """Rewind a session to a specific UUIDv7 checkpoint ID."""
        return self._svc.rewind_checkpoint(checkpoint_id)


class _DocsNamespace:
    """SDK namespace for documentation generation."""

    def __init__(self):
        from src.core.services import docs_service
        self._svc = docs_service

    def generate(
        self,
        workspace_path: str,
        site_name: str,
        pages: List[Dict[str, str]],
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate MkDocs scaffold."""
        return self._svc.generate_mkdocs(
            workspace_path=workspace_path,
            site_name=site_name,
            pages=pages,
            **kwargs,
        )


class _FactoryNamespace:
    """SDK namespace for building platforms."""
    
    def __init__(self):
        from src.core.services import orchestration_service
        self._svc = orchestration_service.OrchestrationService()

    async def build(self, user_id: str, session_id: str, intent: str) -> Dict[str, Any]:
        """Trigger a factory build for a new agent platform."""
        return await self._svc.run_persona_graph(user_id, session_id, intent)


class CoReasonClient:
    """
    In-process Python SDK for the CoReason platform.
    Provides direct access to all platform capabilities without HTTP overhead.

    Usage:
        client = CoReasonClient()
        agents = client.agents.list()
        health = await client.health()
    """

    def __init__(self):
        self.projects = _ProjectsNamespace()
        self.agents = _AgentsNamespace()
        self.docs = _DocsNamespace()
        self.factory = _FactoryNamespace()

    async def health(self) -> Dict[str, Any]:
        """Run platform health check."""
        from src.core.services import health_service
        return await health_service.check()

    def version(self) -> Dict[str, str]:
        """Get platform version info."""
        from src.core.services import health_service
        return health_service.get_version()
