"""
Core Services Layer — Single Source of Truth for all business logic.
All interaction surfaces (API, CLI, MCP, SDK, Streaming) delegate here.
"""
from src.core.services.health_service import HealthService
from src.core.services.project_service import ProjectService
from src.core.services.agent_service import AgentService
from src.core.services.docs_service import DocsService

# Singleton service instances — shared across all surfaces
health_service = HealthService()
project_service = ProjectService()
agent_service = AgentService()
docs_service = DocsService()

__all__ = [
    "health_service",
    "project_service",
    "agent_service",
    "docs_service",
]
