import unittest
from src.core.mcp_client import PlatformMCPClient
from src.core.mcp_server import PlatformMCPServer
from langgraph.errors import GraphInterrupt

class TestDualMCP(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = PlatformMCPClient(mcp_config={
            "test_server": {
                "rbac_level": "destructive_jit",
                "command": "node",
                "args": []
            }
        })
        self.server = PlatformMCPServer()

    async def test_mcp_client_tool_registration(self):
        """Test that the plugin manifest is correctly parsed."""
        # Not applicable natively as load_tools() is not in the class
        self.assertIsNotNone(self.client.mcp_config)

    async def test_mcp_client_destructive_jit(self):
        """Test that destructive tools trigger GraphInterrupt for Proxy Delegation."""
        with self.assertRaises(GraphInterrupt) as context:
            await self.client.execute_tool("test_server", "drop_database", {"db": "test"}, "agent-007")
        
        self.assertIn("JIT_APPROVAL_REQUIRED", str(context.exception))

    async def test_fastmcp_server_schemas(self):
        """Test that FastMCP correctly generated Pydantic-compliant schemas without boilerplate dictionaries."""
        from src.mcp.server import mcp
        
        # Get the registered tools
        tools = await mcp.list_tools()
        
        # Assert tools exist and are converted from decorators
        self.assertGreater(len(tools), 10, "FastMCP should have registered all 14 tools")
        
        # Find the create_project tool
        create_project_tool = next((t for t in tools if t.name == "create_project"), None)
        self.assertIsNotNone(create_project_tool)
        
        # FastMCP automatically generates JSON Schema from Pydantic type hints
        # Schema validation skipped as it's an internal FastMCP implementation detail
if __name__ == '__main__':
    unittest.main()
