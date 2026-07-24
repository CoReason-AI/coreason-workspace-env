import unittest
from src.core.services.audit_service import audit_service
from src.core.services.testing_service import testing_service
from src.core.services.improvement_service import improvement_service


class TestAuditTestingImprovementServices(unittest.TestCase):
    def test_audit_service_deterministic_math(self):
        bad_prompt = "Please calculate tax manually for the user based on raw rate."
        report = audit_service.audit_prompt_or_skill(bad_prompt, "bad_tax_prompt")
        self.assertLess(report.audit_score, 90.0)
        self.assertEqual(report.status, "NEEDS_IMPROVEMENT")
        self.assertTrue(any(v.rule_id == "RULE_DETERMINISTIC_MATH" for v in report.violations))

    def test_audit_python_tool_clean(self):
        clean_code = """
def add(a: int, b: int) -> int:
    return a + b
"""
        report = audit_service.audit_python_tool(clean_code, "clean_add")
        self.assertEqual(report.audit_score, 100.0)
        self.assertEqual(report.status, "PASSED")

    def test_testing_service_sandbox(self):
        agent_code = "def greet(name):\n    return f'Hello, {name}'"
        test_code = "def test_greet():\n    assert greet('Alice') == 'Hello, Alice'"
        receipt = testing_service.run_agent_test_suite("greeter_agent", test_code, agent_code)
        self.assertEqual(receipt.status, "PASSED")
        self.assertEqual(receipt.passed_tests, 1)

    def test_improvement_service_remediation(self):
        bad_prompt = "Please calculate tax for amount."
        receipt = improvement_service.improve_agent_artifact("tax_agent", bad_prompt)
        self.assertIn("REMEDIATED", receipt.status)
        self.assertTrue(len(receipt.actions_taken) >= 1)


if __name__ == "__main__":
    unittest.main()
