"""
Tests for multi-surface parity.
Verifies CLI, MCP Server, Python SDK, and API router all work correctly.
"""
import unittest
import json
import subprocess
import sys
from unittest.mock import patch, MagicMock


class TestCLISurface(unittest.TestCase):
    """Test that the CLI surface works and mirrors the API."""

    def _run_cli(self, *args):
        """Helper to run a CLI command and return parsed JSON output."""
        cmd = [sys.executable, "-m", "src.cli.main", "--pretty"] + list(args)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=".",
        )
        return result

    def test_cli_help(self):
        """CLI should show help without error."""
        result = self._run_cli("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("coreason", result.stdout.lower())

    def test_cli_agents_list(self):
        """CLI agents list should return valid JSON with agents."""
        result = self._run_cli("agents", "list")
        self.assertEqual(result.returncode, 0, f"stderr: {result.stderr}")
        data = json.loads(result.stdout)
        self.assertIn("agents", data)
        self.assertGreater(len(data["agents"]), 0)

    def test_cli_agents_get(self):
        """CLI agents get should return a specific agent."""
        result = self._run_cli("agents", "get", "--name", "factory_ceo")
        self.assertEqual(result.returncode, 0, f"stderr: {result.stderr}")
        data = json.loads(result.stdout)
        self.assertIn("agent", data)
        self.assertEqual(data["agent"]["name"], "factory_ceo")

    def test_cli_agents_get_nonexistent(self):
        """CLI agents get for nonexistent agent should fail."""
        result = self._run_cli("agents", "get", "--name", "nonexistent_xyz")
        self.assertNotEqual(result.returncode, 0)

    def test_cli_mcp_list_servers(self):
        """CLI mcp list-servers should return servers."""
        result = self._run_cli("mcp", "list-servers")
        self.assertEqual(result.returncode, 0, f"stderr: {result.stderr}")
        data = json.loads(result.stdout)
        self.assertIn("servers", data)
        self.assertGreater(len(data["servers"]), 0)

    def test_cli_structured_json_output(self):
        """CLI without --pretty should return compact JSON."""
        cmd = [sys.executable, "-m", "src.cli.main", "agents", "list"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=".",
        )
        self.assertEqual(result.returncode, 0)
        # Compact JSON should be a single line
        lines = [l for l in result.stdout.strip().split("\n") if l.strip()]
        self.assertEqual(len(lines), 1, "Compact JSON should be a single line")
        data = json.loads(result.stdout)
        self.assertIn("agents", data)


class TestSDKSurface(unittest.TestCase):
    """Test the Python SDK surface."""

    def test_sdk_import(self):
        """CoReasonClient should be importable."""
        from src.sdk import CoReasonClient
        client = CoReasonClient()
        self.assertIsNotNone(client)

    def test_sdk_agents_list(self):
        """SDK agents.list() should return agents."""
        from src.sdk import CoReasonClient
        client = CoReasonClient()
        agents = client.agents.list()
        self.assertIsInstance(agents, list)
        self.assertGreater(len(agents), 0)

    def test_sdk_agents_get(self):
        """SDK agents.get() should return a specific agent."""
        from src.sdk import CoReasonClient
        client = CoReasonClient()
        agent = client.agents.get("factory_ceo")
        self.assertIsNotNone(agent)
        self.assertEqual(agent["name"], "factory_ceo")

    def test_sdk_agents_get_nonexistent(self):
        """SDK agents.get() should return None for nonexistent."""
        from src.sdk import CoReasonClient
        client = CoReasonClient()
        agent = client.agents.get("nonexistent_xyz")
        self.assertIsNone(agent)

    def test_sdk_mcp_list_servers(self):
        """SDK mcp.list_servers() should return servers."""
        from src.sdk import CoReasonClient
        client = CoReasonClient()
        servers = client.mcp.list_servers()
        self.assertIsInstance(servers, list)
        self.assertGreater(len(servers), 0)

    def test_sdk_version(self):
        """SDK version() should return platform info."""
        from src.sdk import CoReasonClient
        client = CoReasonClient()
        info = client.version()
        self.assertIn("version", info)
        self.assertIn("platform", info)

    def test_sdk_namespaces_exist(self):
        """SDK should have all namespace properties."""
        from src.sdk import CoReasonClient
        client = CoReasonClient()
        self.assertTrue(hasattr(client, "projects"))
        self.assertTrue(hasattr(client, "agents"))
        self.assertTrue(hasattr(client, "mcp"))
        self.assertTrue(hasattr(client, "docs"))


class TestMCPServerSurface(unittest.TestCase):
    """Test the MCP server tool registration."""

    def test_mcp_server_builds(self):
        """MCP server should build without error."""
        from src.mcp.server import _build_server
        server = _build_server()
        self.assertIsNotNone(server)

    def test_mcp_server_name(self):
        """MCP server should have the correct name."""
        from src.mcp.server import _build_server
        server = _build_server()
        self.assertEqual(server.name, "coreason-platform")


class TestAPIRouter(unittest.TestCase):
    """Test that the API router registers all expected routes."""

    def test_router_import(self):
        """Router should import without error."""
        from src.api.router import api_router
        self.assertIsNotNone(api_router)

    def test_router_has_routes(self):
        """Router should have registered routes."""
        from src.api.router import api_router
        self.assertGreater(len(api_router.routes), 0)

    def test_router_includes_all_tags(self):
        """Router should include routes from all endpoint modules."""
        from src.api.router import api_router
        route_paths = []
        for route in api_router.routes:
            if hasattr(route, "path"):
                route_paths.append(route.path)
        # Check key paths exist
        path_str = " ".join(route_paths)
        self.assertIn("/projects", path_str)
        self.assertIn("/agents", path_str)
        self.assertIn("/mcp", path_str)
        self.assertIn("/docs", path_str)


class TestStreamingModules(unittest.TestCase):
    """Test that streaming modules import correctly."""

    def test_crdt_router_import(self):
        from src.api.streaming.crdt import router
        self.assertIsNotNone(router)

    def test_tty_router_import(self):
        from src.api.streaming.tty import router
        self.assertIsNotNone(router)

    def test_state_sync_router_import(self):
        from src.api.streaming.state_sync import router
        self.assertIsNotNone(router)

    def test_agent_progress_router_import(self):
        from src.api.streaming.agent_progress import router
        self.assertIsNotNone(router)


class TestParityConsistency(unittest.TestCase):
    """
    Cross-surface parity tests — verifies that all surfaces
    return the same data for equivalent operations.
    """

    def test_agents_list_parity_sdk_vs_service(self):
        """SDK and service layer should return identical agent lists."""
        from src.sdk import CoReasonClient
        from src.core.services import agent_service

        sdk_agents = CoReasonClient().agents.list()
        svc_agents = agent_service.list_agents()

        sdk_names = sorted([a["name"] for a in sdk_agents])
        svc_names = sorted([a["name"] for a in svc_agents])
        self.assertEqual(sdk_names, svc_names)

    def test_mcp_servers_parity_sdk_vs_service(self):
        """SDK and service layer should return identical MCP server lists."""
        from src.sdk import CoReasonClient
        from src.core.services import mcp_tool_service

        sdk_servers = CoReasonClient().mcp.list_servers()
        svc_servers = mcp_tool_service.list_servers()

        sdk_names = sorted([s["name"] for s in sdk_servers])
        svc_names = sorted([s["name"] for s in svc_servers])
        self.assertEqual(sdk_names, svc_names)

    def test_agents_list_parity_cli_vs_sdk(self):
        """CLI and SDK should return the same agent names."""
        import subprocess, sys
        from src.sdk import CoReasonClient

        # Get from CLI
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.main", "agents", "list"],
            capture_output=True, text=True,
            cwd=".",
        )
        cli_data = json.loads(result.stdout)
        cli_names = sorted([a["name"] for a in cli_data["agents"]])

        # Get from SDK
        sdk_names = sorted([a["name"] for a in CoReasonClient().agents.list()])

        self.assertEqual(cli_names, sdk_names)


if __name__ == "__main__":
    unittest.main()
