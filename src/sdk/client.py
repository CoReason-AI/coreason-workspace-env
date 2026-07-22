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



    async def list(self) -> List[Dict[str, Any]]:
        """List all projects."""
        from src.core.adapters.dify_adapter import DifyAdapter
        adapter = DifyAdapter()
        try:
            res = await adapter.get_workspace_info()
            return [res]
        except Exception:
            return []
        finally:
            await adapter.close()

    async def create(self, name: str, description: str = "",
                     config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new project/workspace."""
        from src.core.adapters.dify_adapter import DifyAdapter
        adapter = DifyAdapter()
        try:
            return await adapter.create_workspace(name, description)
        finally:
            await adapter.close()

    async def get(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get a project by ID."""
        # Dify workspaces typically don't have a single ID fetch that isn't /info for the current key
        from src.core.adapters.dify_adapter import DifyAdapter
        adapter = DifyAdapter()
        try:
            return await adapter.get_workspace_info()
        finally:
            await adapter.close()

    async def delete(self, project_id: str) -> bool:
        """Delete a project/workspace by ID."""
        from src.core.adapters.dify_adapter import DifyAdapter
        adapter = DifyAdapter()
        try:
            return await adapter.delete_workspace(project_id)
        finally:
            await adapter.close()

    async def export(self, project_path: str, output_path: str, skip_state: bool = False, skip_docker: bool = False) -> Dict[str, Any]:
        """Export a project for air-gapped transfer."""
        from src.core.adapters.dify_adapter import DifyAdapter
        adapter = DifyAdapter()
        try:
            res = await adapter.export_app(project_path)  # Assuming project_path is app_id
            with open(output_path, "w") as f:
                json.dump(res, f)
            return {"status": "exported", "path": output_path}
        finally:
            await adapter.close()

    async def import_bundle(self, import_path: str, name: str, description: str = "",
                            config: Optional[Dict[str, Any]] = None, skip_state: bool = False, skip_docker: bool = False) -> Dict[str, Any]:
        """Import a project from an air-gapped export bundle."""
        from src.core.adapters.dify_adapter import DifyAdapter
        adapter = DifyAdapter()
        try:
            with open(import_path, "r") as f:
                data = json.load(f)
            return await adapter.import_app(data)
        finally:
            await adapter.close()


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




class _FactoryNamespace:
    """SDK namespace for building platforms."""


    async def build(self, user_id: str, session_id: str, intent: str) -> Dict[str, Any]:
        """Trigger a factory build for a new agent platform."""
        from src.core.services.agent_service import AgentService
        agent_service = AgentService()
        return await agent_service.execute_agent("factory_ceo", {"intent": intent}, user_id, "sdk-tenant", session_id)


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
        self.factory = _FactoryNamespace()

    async def health(self) -> Dict[str, Any]:
        """Run platform health check."""
        from src.core.services import health_service
        return await health_service.check()

    def version(self) -> Dict[str, str]:
        """Get platform version info."""
        from src.core.services import health_service
        return health_service.get_version()
