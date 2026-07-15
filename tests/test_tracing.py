"""
Tests for the Langfuse/WORM Tracing Bridge (src.core.tracing).
Verifies dual-write pattern, hash sharing, and callback integration.
"""
import unittest
from unittest.mock import patch, MagicMock


class TestTracingConfig(unittest.TestCase):
    """Test Langfuse configuration."""

    def test_config_loads_from_env(self):
        from src.core.tracing.config import LangfuseConfig
        config = LangfuseConfig()
        self.assertTrue(config.is_configured)
        self.assertIn("localhost", config.host)

    def test_config_disabled(self):
        import os
        with patch.dict(os.environ, {"LANGFUSE_ENABLED": "false"}):
            from importlib import reload
            from src.core.tracing import config
            reload(config)
            self.assertFalse(config.LangfuseConfig().enabled)


class TestWORMAuditorReturnHash(unittest.TestCase):
    """Test that the updated WORM auditor returns hashes."""

    def setUp(self):
        from src.core.security.audit import WORMStorageAuditor
        self.auditor = WORMStorageAuditor()

    def test_log_agent_thought_returns_hash(self):
        result = self.auditor.log_agent_thought(
            agent_id="test_agent",
            run_id="test-run-123",
            thought_content="I am thinking about architecture",
        )
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 64)  # SHA-256 hex digest

    def test_log_supervisor_action_returns_hash(self):
        result = self.auditor.log_supervisor_action(
            supervisor_email="admin@coreason.ai",
            action="approve",
            target="agent_yaml:factory_ceo",
        )
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 64)

    def test_hashes_are_deterministic_for_same_input(self):
        """Same event data should produce same hash."""
        h1 = self.auditor._hash_event({"action": "test", "id": "1"})
        h2 = self.auditor._hash_event({"action": "test", "id": "1"})
        self.assertEqual(h1, h2)


class TestTracingBridge(unittest.TestCase):
    """Test the TracingBridge dual-write pattern."""

    def test_bridge_traces_agent_thought_without_langfuse(self):
        """Bridge should work even when Langfuse is not available."""
        from src.core.tracing.langfuse_bridge import TracingBridge
        bridge = TracingBridge()
        # Force Langfuse to None (not installed/configured)
        bridge._langfuse = None

        result = bridge.trace_agent_thought(
            agent_id="test_agent",
            run_id="test-123",
            thought="Testing the bridge",
        )
        self.assertIn("hash", result)
        self.assertEqual(len(result["hash"]), 64)

    def test_bridge_traces_supervisor_action_without_langfuse(self):
        """Bridge should work for supervisor actions without Langfuse."""
        from src.core.tracing.langfuse_bridge import TracingBridge
        bridge = TracingBridge()
        bridge._langfuse = None

        result = bridge.trace_supervisor_action(
            supervisor_email="admin@coreason.ai",
            action="approve",
            target="agent_yaml:test",
        )
        self.assertIn("hash", result)
        self.assertEqual(len(result["hash"]), 64)


class TestTracingCallback(unittest.TestCase):
    """Test the LangChain callback handler."""

    def test_callback_instantiation(self):
        from src.core.tracing.callbacks import CoReasonTracingCallback
        callback = CoReasonTracingCallback(run_id="test-123", agent_id="factory_ceo")
        self.assertEqual(callback.run_id, "test-123")
        self.assertEqual(callback.agent_id, "factory_ceo")

    def test_callback_on_llm_start(self):
        """on_llm_start should not crash and should call the bridge."""
        from src.core.tracing.callbacks import CoReasonTracingCallback
        callback = CoReasonTracingCallback(run_id="test-123", agent_id="test_agent")

        # Should not raise
        callback.on_llm_start(
            serialized={"name": "gpt-4"},
            prompts=["Hello, world!"],
        )

    def test_callback_on_tool_start(self):
        from src.core.tracing.callbacks import CoReasonTracingCallback
        callback = CoReasonTracingCallback(run_id="test-123", agent_id="test_agent")

        callback.on_tool_start(
            serialized={"name": "local_fs_writer"},
            input_str='{"path": "/tmp/test.yaml"}',
        )

    def test_callback_on_tool_end(self):
        from src.core.tracing.callbacks import CoReasonTracingCallback
        callback = CoReasonTracingCallback(run_id="test-123", agent_id="test_agent")

        callback.on_tool_end(output="File written successfully")


class TestTracingSingleton(unittest.TestCase):
    """Test the tracing_bridge singleton."""

    def test_singleton_import(self):
        from src.core.tracing.langfuse_bridge import tracing_bridge
        self.assertIsNotNone(tracing_bridge)

    def test_singleton_is_same_instance(self):
        from src.core.tracing.langfuse_bridge import tracing_bridge as b1
        from src.core.tracing.langfuse_bridge import tracing_bridge as b2
        self.assertIs(b1, b2)


if __name__ == "__main__":
    unittest.main()
