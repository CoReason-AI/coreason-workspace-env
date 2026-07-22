"""
Tests for the shared service layer (src.core.services).
Tests agent discovery, MCP service, docs generation, and health service.
Postgres-dependent tests (project_service) are separated into async integration tests.
"""
import unittest
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock


class TestAgentService(unittest.TestCase):
    """Test agent discovery and introspection from YAML manifests."""

    def setUp(self):
        from src.core.services.agent_service import AgentService
        self.service = AgentService()

    def test_list_agents_returns_all(self):
        """All agents in src/agents/ should be discovered."""
        agents = self.service.list_agents()
        self.assertIsInstance(agents, list)
        self.assertGreater(len(agents), 0)

    def test_list_agents_contains_factory_ceo(self):
        """factory_ceo must always be discoverable."""
        agents = self.service.list_agents()
        names = [a["name"] for a in agents]
        self.assertIn("factory_ceo", names)

    def test_list_agents_schema(self):
        """Every agent must have required fields."""
        agents = self.service.list_agents()
        for agent in agents:
            self.assertIn("name", agent)
            self.assertIn("type", agent)
            self.assertIn("description", agent)
            # Support both skill_registry (new) and skills (legacy)
            has_skills = "skills" in agent or "skill_registry" in agent
            self.assertTrue(has_skills, f"Agent {agent['name']} missing skills or skill_registry")
            self.assertIn("dependencies", agent)
            self.assertIn("path", agent)
            self.assertIsInstance(agent["dependencies"], list)

    def test_get_agent_existing(self):
        """get_agent should return full manifest for an existing agent."""
        agent = self.service.get_agent("factory_ceo")
        self.assertIsNotNone(agent)
        self.assertEqual(agent["name"], "factory_ceo")
        self.assertEqual(agent["type"], "supervisor")
        self.assertIn("system_prompt", agent)
        self.assertTrue(len(agent["system_prompt"]) > 0)

    def test_get_agent_nonexistent(self):
        """get_agent should return None for a nonexistent agent."""
        agent = self.service.get_agent("nonexistent_agent_xyz")
        self.assertIsNone(agent)

    def test_get_agent_includes_orchestrator(self):
        """get_agent should include orchestrator source when available."""
        agent = self.service.get_agent("factory_ceo")
        self.assertIsNotNone(agent)
        # factory_ceo has an orchestrator.py
        self.assertIn("orchestrator_source", agent)


class TestHealthService(unittest.TestCase):
    """Test health service version info (connectivity tests need infra)."""

    def setUp(self):
        from src.core.services.health_service import HealthService
        self.service = HealthService()

    def test_get_version(self):
        """Should return version and platform name."""
        info = self.service.get_version()
        self.assertIn("version", info)
        self.assertIn("platform", info)
        self.assertEqual(info["platform"], "coreason-workspace-env")


class TestServiceSingletons(unittest.TestCase):
    """Test that the __init__.py exports work correctly."""

    def test_all_singletons_importable(self):
        from src.core.services import (
            health_service,
            agent_service,
        )
        self.assertIsNotNone(health_service)
        self.assertIsNotNone(agent_service)


if __name__ == "__main__":
    unittest.main()
