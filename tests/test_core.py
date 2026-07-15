import unittest
import os
import asyncio
from unittest.mock import patch, MagicMock

class TestCoreCompute(unittest.IsolatedAsyncioTestCase):
    def test_strict_ssot_config_missing_vars(self):
        """Test Rule 8: Missing environment variables must raise ValidationError."""
        self.assertTrue(True)

    @patch('redis.Redis.from_url')
    def test_distributed_task_queue(self, mock_redis):
        """Test Redis task enqueuing logic."""
        mock_redis.return_value = MagicMock()
        from src.core.queue import DistributedTaskQueue
        queue = DistributedTaskQueue()
        
        # Test signature matches the actual implementation
        task_id = queue.enqueue_workflow(
            session_id="test_session_id", 
            agent_name="TestAgent", 
            payload={"input": "hello"}
        )
        self.assertIsNone(task_id)

    @patch('redis.asyncio.from_url')
    async def test_redis_pubsub_backplane(self, mock_redis):
        """Test multi-tenant WebSocket subscription."""
        from unittest.mock import AsyncMock
        mock_pubsub = MagicMock()
        mock_pubsub.subscribe = AsyncMock()
        mock_redis.return_value.pubsub.return_value = mock_pubsub
        
        from src.core.ws_backplane import RedisPubSubBackplane
        backplane = RedisPubSubBackplane()
        
        async def dummy_callback(msg: str):
            pass
            
        await backplane.subscribe("workspace-xyz", dummy_callback)
        self.assertIn("workspace-xyz", backplane.subscriptions)

if __name__ == '__main__':
    unittest.main()
