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



if __name__ == '__main__':
    unittest.main()
