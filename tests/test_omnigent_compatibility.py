import os
from pathlib import Path
import yaml
import unittest

class TestOmnigentCompatibility(unittest.TestCase):
    """Ensure all factory agents are natively compatible with the Omnigent meta-harness."""

    def setUp(self):
        self.agents_dir = Path(__file__).resolve().parent.parent / "src" / "agents"

    def test_all_agents_have_omnigent_executor(self):
        """All agents must declare an executor block with a harness and model."""
        agents = [d for d in self.agents_dir.iterdir() if d.is_dir() and (d / "agent.yaml").exists()]
        self.assertTrue(len(agents) > 0, "No agents found in src/agents/")

        for agent_dir in agents:
            yaml_path = agent_dir / "agent.yaml"
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            agent_name = agent_dir.name
            
            # 1. Check executor exists
            self.assertIn("executor", data, f"Agent '{agent_name}' missing 'executor' block for Omnigent compatibility.")
            executor = data["executor"]
            self.assertIsInstance(executor, dict, f"Agent '{agent_name}' executor must be a dictionary.")
            
            # 2. Check harness and model
            self.assertIn("harness", executor, f"Agent '{agent_name}' executor missing 'harness'.")
            self.assertIn("model", executor, f"Agent '{agent_name}' executor missing 'model'.")
            
            # 3. Check async and cancellable
            self.assertTrue(data.get("async", False), f"Agent '{agent_name}' missing 'async: true'.")
            self.assertTrue(data.get("cancellable", False), f"Agent '{agent_name}' missing 'cancellable: true'.")
            
            # 4. Check os_env for sandbox support
            # Since all factory agents might need local execution (or we default them to caller_process)
            self.assertIn("os_env", data, f"Agent '{agent_name}' missing 'os_env' block for OpenShell sandboxing.")
            os_env = data["os_env"]
            self.assertIsInstance(os_env, dict, f"Agent '{agent_name}' os_env must be a dictionary.")

if __name__ == "__main__":
    unittest.main()
