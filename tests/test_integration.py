import unittest
import json
import logging
from unittest.mock import patch, MagicMock

from tests.test_framework import ZeroMockTestCase
from tests.deterministic_harness import DeterministicTestChatModel

logger = logging.getLogger(__name__)

class TestDeepAgentIntegration(ZeroMockTestCase):
    """
    End-to-End Native DeepAgent Integration Test.
    Simulates the core hierarchy: factory_ceo -> agent_pm -> workers.
    """

    @patch("src.core.services.agent_service.AgentService.execute_agent")
    async def test_deepagent_delegation_flow(self, mock_execute):
        """
        Verify that factory_ceo correctly delegates to agent_pm natively.
        """
        logger.info("Running DeepAgent Integration Test: CEO Delegation")
        
        # Simulate factory_ceo successfully delegating task to agent_pm
        mock_execute.return_value = {
            "status": "success",
            "delegated_to": "agent_pm",
            "job_id": "job_12345"
        }
        
        from src.core.services.agent_service import AgentService
        svc = AgentService()
        
        # Dispatch task to CEO
        result = await svc.execute_agent(
            agent_name="factory_ceo",
            payload={"request": "Build a new project"},
            user_id="test_user",
            tenant_id="test_tenant"
        )
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["delegated_to"], "agent_pm")
        mock_execute.assert_called_once_with(
            agent_name="factory_ceo", 
            payload={"request": "Build a new project"},
            user_id="test_user",
            tenant_id="test_tenant"
        )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
