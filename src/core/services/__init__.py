"""
Core Services Layer — Single Source of Truth for all business logic.
All interaction surfaces (API, CLI, MCP, SDK, Streaming) delegate here.
"""
from src.core.services.health_service import HealthService
from src.core.services.agent_service import AgentService
from src.core.services.trace_service import trace_service
from src.core.services.skill_service import skill_service
from src.core.services.sandbox_service import sandbox_service
from src.core.services.catalog_service import catalog_service

# Singleton service instances — shared across all surfaces
health_service = HealthService()
agent_service = AgentService()

__all__ = [
    "health_service",
    "agent_service",
    "trace_service",
    "skill_service",
    "sandbox_service",
    "catalog_service",
]
