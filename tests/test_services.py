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

    def test_list_agents_contains_agent_validator(self):
        """agent_validator must be discoverable (created in Maker-Checker split)."""
        agents = self.service.list_agents()
        names = [a["name"] for a in agents]
        self.assertIn("agent_validator", names)

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

    def test_agent_validator_skills_are_validation(self):
        """agent_validator must reference validation/ standards."""
        agent = self.service.get_agent("agent_validator")
        self.assertIsNotNone(agent)
        # After migration, uses skill_registry
        if "skill_registry" in agent:
            for entry in agent["skill_registry"]:
                self.assertIn("validation", entry["path"], f"Validator entry {entry['name']} should reference validation/")
        else:
            for skill in agent.get("skills", []):
                self.assertIn("validation", skill, f"Validator skill {skill} should reference validation/")

    def test_factory_ceo_skills_are_building(self):
        """factory_ceo must reference building/ standards."""
        agent = self.service.get_agent("factory_ceo")
        self.assertIsNotNone(agent)
        # After migration, uses skill_registry
        if "skill_registry" in agent:
            for entry in agent["skill_registry"]:
                self.assertIn("building", entry["path"], f"Builder entry {entry['name']} should reference building/")
        else:
            for skill in agent.get("skills", []):
                self.assertIn("building", skill, f"Builder skill {skill} should reference building/")


class TestMCPToolService(unittest.TestCase):
    """Test MCP server discovery."""

    def setUp(self):
        from src.core.services.mcp_service import MCPToolService
        self.service = MCPToolService()

    def test_list_servers(self):
        """Should return at least the platform MCP server."""
        servers = self.service.list_servers()
        self.assertIsInstance(servers, list)
        self.assertGreater(len(servers), 0)

    def test_server_schema(self):
        """Each server should have required fields."""
        servers = self.service.list_servers()
        for server in servers:
            self.assertIn("name", server)
            self.assertIn("transport", server)
            self.assertIn("description", server)
            self.assertIn("tools", server)


class TestDocsService(unittest.TestCase):
    """Test MkDocs generation service."""

    def setUp(self):
        from src.core.services.docs_service import DocsService
        self.service = DocsService()
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_generate_mkdocs_creates_files(self):
        """Should create mkdocs.yml and markdown pages."""
        workspace = os.path.join(self.tmpdir, "test_docs")
        result = self.service.generate_mkdocs(
            workspace_path=workspace,
            site_name="Test Site",
            pages=[
                {"title": "Home", "filename": "index.md", "content": "# Hello"},
                {"title": "About", "filename": "about.md", "content": "# About"},
            ],
        )
        self.assertEqual(result["status"], "success")
        self.assertTrue(os.path.exists(os.path.join(workspace, "mkdocs.yml")))
        self.assertTrue(os.path.exists(os.path.join(workspace, "docs", "index.md")))
        self.assertTrue(os.path.exists(os.path.join(workspace, "docs", "about.md")))

    def test_generate_mkdocs_relative_path_rejected(self):
        """Relative paths should be rejected."""
        result = self.service.generate_mkdocs(
            workspace_path="relative/path",
            site_name="Test",
            pages=[],
        )
        self.assertEqual(result["status"], "error")

    def test_generate_mkdocs_nav_auto_generated(self):
        """Nav should be auto-generated from pages if not provided."""
        import yaml
        workspace = os.path.join(self.tmpdir, "test_nav")
        self.service.generate_mkdocs(
            workspace_path=workspace,
            site_name="Nav Test",
            pages=[{"title": "Home", "filename": "index.md", "content": "# Hi"}],
        )
        with open(os.path.join(workspace, "mkdocs.yml")) as f:
            config = yaml.safe_load(f)
        self.assertEqual(config["nav"], [{"Home": "index.md"}])


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
            project_service,
            agent_service,
            mcp_tool_service,
            docs_service,
        )
        self.assertIsNotNone(health_service)
        self.assertIsNotNone(project_service)
        self.assertIsNotNone(agent_service)
        self.assertIsNotNone(mcp_tool_service)
        self.assertIsNotNone(docs_service)


if __name__ == "__main__":
    unittest.main()
