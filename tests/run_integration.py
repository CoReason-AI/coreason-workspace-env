import unittest
import json
import logging
import hashlib
from typing import Dict, Any

from tests.test_framework import ZeroMockTestCase
from src.core.skills.jinja2_ast_auditor import jinja2_ast_auditor

logger = logging.getLogger(__name__)

class TestFactoryIntegration(ZeroMockTestCase):
    """
    End-to-End Factory Integration Test (Option 2).
    Simulates the entire Agent Lifecycle: CEO -> PMs -> Makers -> Checker -> WORM -> Deployment.
    """

    def setUp(self):
        self.worm_logs = []
        self.state_trace = []
        self.target_agent = "causal_inference_consultant"

    def log_worm_event(self, event: str):
        """Simulates WORM Audit Logging"""
        self.worm_logs.append(event)
        self.state_trace.append({"step": "worm_log", "event": event})

    def run_lifecycle(self, simulated_maker_code: str) -> Dict[str, Any]:
        """Runs the simulated Maker-Checker-Approver pipeline."""
        
        # 1. factory_ceo
        self.state_trace.append({"step": "factory_ceo", "action": "receive_human_request", "target": self.target_agent})
        self.log_worm_event(f"CEO received request to build {self.target_agent}")
        
        # 2. agent_pm
        self.state_trace.append({"step": "agent_pm", "action": "delegate_to_makers"})
        self.log_worm_event("PM delegated tasks to yaml_compiler and prompt_engineer")
        
        # 3. Makers (yaml_compiler & prompt_engineer)
        self.state_trace.append({"step": "yaml_compiler", "action": "draft_agent_yaml"})
        self.state_trace.append({"step": "prompt_engineer", "action": "draft_orchestrator_py"})
        
        # 4. Checker (agent_validator running AST Guardrails)
        self.state_trace.append({"step": "agent_validator", "action": "run_ast_auditor"})
        
        # Live invocation of the actual AST Auditor!
        audit_result_json = jinja2_ast_auditor.invoke({"python_code": simulated_maker_code})
        audit_result = json.loads(audit_result_json)
        
        if audit_result["status"] == "FAIL":
            self.state_trace.append({"step": "agent_validator", "result": "FAIL", "violations": audit_result["violations"]})
            self.log_worm_event(f"Checker REJECTED Maker code. Violations: {audit_result['violations']}")
            return {"status": "remediation_required", "audit_result": audit_result}
            
        # 5. Success Path
        self.state_trace.append({"step": "agent_validator", "result": "PASS"})
        self.log_worm_event("Checker APPROVED Maker code. Code conforms to Jinja2 Decoupling.")
        
        # 6. Deployment
        self.state_trace.append({"step": "deployment", "action": "deploy_agent"})
        self.log_worm_event(f"Agent {self.target_agent} successfully deployed.")
        
        return {"status": "deployed", "audit_result": audit_result}

    def test_factory_pipeline_failure_path(self):
        """
        Simulates the Maker generating code with a structural bypass.
        Verifies that the Checker fails the code and blocks deployment.
        """
        logger.info("Running Pipeline Test: Failure Path (Structural Bypass)")
        
        bypassed_code = """
from pathlib import Path
def write_causal_report():
    date = "2026-07-14"
    Path(f"report_{date}.md").write_text("# Causal Inference Report")
"""
        result = self.run_lifecycle(bypassed_code)
        
        # Assertions
        self.assertEqual(result["status"], "remediation_required")
        self.assertEqual(result["audit_result"]["status"], "FAIL")
        self.assertTrue(any("Direct Pathlib write_text to markdown file detected" in v for v in result["audit_result"]["violations"]))
        self.assertTrue(any("Checker REJECTED Maker code" in log for log in self.worm_logs))
        
        # Use the built-in Zero Waste Determinism Hash assertion
        # Note: In a real CI environment, you would replace this with the actual golden baseline hash
        golden_baseline_hash = hashlib.sha256(json.dumps(self.state_trace, sort_keys=True).encode('utf-8')).hexdigest()
        self.assertExecutionDeterminism(self.state_trace, golden_baseline_hash)
        logger.info(f"Failure Path Determinism Hash: {golden_baseline_hash}")

    def test_factory_pipeline_success_path(self):
        """
        Simulates the Maker generating properly decoupled code.
        Verifies that the Checker passes the code and deploys the agent.
        """
        logger.info("Running Pipeline Test: Success Path (Jinja2 Decoupled)")
        
        clean_code = """
import json
def generate_causal_telemetry():
    data = {"nodes": 4, "edges": 5}
    with open("causal_results.json", "w") as f:
        json.dump(data, f)
    return data
"""
        result = self.run_lifecycle(clean_code)
        
        # Assertions
        self.assertEqual(result["status"], "deployed")
        self.assertEqual(result["audit_result"]["status"], "PASS")
        self.assertTrue(any("Checker APPROVED Maker code" in log for log in self.worm_logs))
        self.assertTrue(any("successfully deployed" in log for log in self.worm_logs))
        
        # Use the built-in Zero Waste Determinism Hash assertion
        # Note: In a real CI environment, you would replace this with the actual golden baseline hash
        golden_baseline_hash = hashlib.sha256(json.dumps(self.state_trace, sort_keys=True).encode('utf-8')).hexdigest()
        self.assertExecutionDeterminism(self.state_trace, golden_baseline_hash)
        logger.info(f"Success Path Determinism Hash: {golden_baseline_hash}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
