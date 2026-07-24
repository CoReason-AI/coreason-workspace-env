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
    trace = client.traces.get(job_id)
    result = await client.agents.execute("yaml_compiler", payload={...}, user_id="u1", tenant_id="t1")
"""
import uuid
import json
from typing import Dict, Any, List, Optional


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

    async def get_status(self, job_id: str) -> Dict[str, Any]:
        """Check the status of an enqueued job."""
        return await self._svc.get_execution_status(job_id)

    def rewind_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """Rewind a session to a specific UUIDv7 checkpoint ID."""
        return self._svc.rewind_checkpoint(checkpoint_id)

    async def evaluate(
        self,
        agent_name: str,
        test_cases: List[Dict[str, Any]],
        user_id: str = "sdk-user",
        tenant_id: str = "sdk-tenant",
    ) -> Dict[str, Any]:
        """Run agent-level evaluation harness."""
        from src.core.testing.agent_harness import agent_test_harness, TestCaseSpec
        specs = [TestCaseSpec(**tc) for tc in test_cases]
        report = await agent_test_harness.run_evaluation(
            agent_name=agent_name,
            test_cases=specs,
            user_id=user_id,
            tenant_id=tenant_id,
        )
        return report.model_dump()


class _TracesNamespace:
    """SDK namespace for execution trace inspection (meta-programming)."""

    def __init__(self):
        from src.core.services import trace_service
        self._svc = trace_service

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get full execution trace for a job."""
        return self._svc.get_trace(job_id)

    def list(self, agent_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """List execution traces."""
        return self._svc.list_traces(agent_name=agent_name)


class _SkillsNamespace:
    """SDK namespace for Markdown skills registry."""

    def __init__(self):
        from src.core.services import skill_service
        self._svc = skill_service

    def list(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available skills."""
        return self._svc.list_skills(category=category)

    def get(self, name: str) -> Optional[Dict[str, Any]]:
        """Get skill metadata and Markdown content."""
        return self._svc.get_skill(name)


class _SandboxesNamespace:
    """SDK namespace for Sandboxed Deployment Environments."""

    def __init__(self):
        from src.core.services import sandbox_service
        self._svc = sandbox_service

    def provision(
        self,
        project_id: str,
        user_id: str = "sdk-user",
        tenant_id: str = "sdk-tenant",
        environment: str = "test",
        secrets: Optional[Dict[str, str]] = None,
        connections: Optional[Dict[str, str]] = None,
        mcp_servers: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Provision a new sandbox environment."""
        rec = self._svc.provision_sandbox(
            project_id=project_id,
            user_id=user_id,
            tenant_id=tenant_id,
            environment=environment,
            secrets=secrets,
            connections=connections,
            mcp_servers=mcp_servers,
        )
        return rec.model_dump()

    def get(self, sandbox_id: str) -> Optional[Dict[str, Any]]:
        """Get details of a sandbox environment."""
        return self._svc.get_sandbox(sandbox_id)

    def list(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List active sandboxes."""
        return self._svc.list_sandboxes(project_id=project_id)

    def execute(self, sandbox_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a payload inside a sandbox."""
        return self._svc.execute_in_sandbox(sandbox_id, payload)

    def terminate(self, sandbox_id: str) -> Dict[str, Any]:
        """Terminate a sandbox."""
        return self._svc.terminate_sandbox(sandbox_id)


class _CatalogNamespace:
    """SDK namespace for URN Catalog Authority (PEN 66197)."""

    def __init__(self):
        from src.core.services import catalog_service
        self._svc = catalog_service

    def search(
        self,
        query: Optional[str] = None,
        resource_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Search the Project & Module Catalog."""
        return self._svc.search_catalog(query=query, resource_type=resource_type, tags=tags)

    def resolve(self, urn: str) -> Optional[Dict[str, Any]]:
        """Resolve an OID or Native URN."""
        return self._svc.resolve_urn(urn)

    def register(
        self,
        urn: str,
        name: str,
        description: str,
        resource_type: str,
        version: str = "1.0.0",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register a project or component in the catalog."""
        entry = self._svc.register_entry(
            urn=urn,
            name=name,
            description=description,
            resource_type=resource_type,
            version=version,
            tags=tags,
            metadata=metadata,
            source_code=source_code,
        )
        return entry.model_dump()

    def import_module(self, urn: str, target_project_id: str) -> Dict[str, Any]:
        """Import a cataloged component into a target project space."""
        return self._svc.import_module(urn, target_project_id)


class CoReasonClient:
    """
    In-process Python SDK for the CoReason platform.
    Provides direct access to all platform capabilities without HTTP overhead.

    Usage:
        client = CoReasonClient()
        agents = client.agents.list()
        skills = client.skills.list()
        catalog = client.catalog.search(query="causal")
        sbx = client.sandboxes.provision(project_id="proj_1")
        trace = client.traces.get(job_id)
        health = await client.health()
    """

    def __init__(self):
        self.agents = _AgentsNamespace()
        self.traces = _TracesNamespace()
        self.skills = _SkillsNamespace()
        self.sandboxes = _SandboxesNamespace()
        self.catalog = _CatalogNamespace()

    async def health(self) -> Dict[str, Any]:
        """Run platform health check."""
        from src.core.services import health_service
        return await health_service.check()

    def version(self) -> Dict[str, str]:
        """Get platform version info."""
        from src.core.services import health_service
        return health_service.get_version()
