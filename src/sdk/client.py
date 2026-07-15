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

    async def export(self, project_path: str, output_path: str) -> Dict[str, Any]:
        """Export a project for air-gapped transfer."""
        return await self._svc.export_project(project_path, output_path)


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


class _MCPNamespace:
    """SDK namespace for MCP server operations."""

    def __init__(self):
        from src.core.services import mcp_tool_service
        self._svc = mcp_tool_service

    def list_servers(self) -> List[Dict[str, Any]]:
        """List configured MCP servers."""
        return self._svc.list_servers()

    async def execute_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any] = None,
        session_id: str = "sdk-session",
    ) -> Dict[str, Any]:
        """Execute an MCP tool."""
        return await self._svc.execute_tool(
            server_name=server_name,
            tool_name=tool_name,
            arguments=arguments or {},
            session_id=session_id,
        )


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
        self.mcp = _MCPNamespace()
        self.docs = _DocsNamespace()

    async def health(self) -> Dict[str, Any]:
        """Run platform health check."""
        from src.core.services import health_service
        return await health_service.check()

    def version(self) -> Dict[str, str]:
        """Get platform version info."""
        from src.core.services import health_service
        return health_service.get_version()
