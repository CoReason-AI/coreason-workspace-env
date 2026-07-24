import unittest
from src.core.services.reasoning_service import reasoning_service
from src.core.tools.reasoning_tools import analogical_mapping_tool, neurosymbolic_deduction_tool


class TestReasoningService(unittest.TestCase):
    def test_analogical_structure_mapping(self):
        res = reasoning_service.perform_analogical_structure_mapping(
            target_problem="How to scale microservice state sync?",
            source_domain="biological_ecosystems",
            target_domain="distributed_cloud_architecture"
        )
        self.assertEqual(res.source_domain, "biological_ecosystems")
        self.assertIn("microservice_instance", res.entity_mappings["organism"])
        self.assertTrue(len(res.relation_mappings) > 0)

    def test_neurosymbolic_deduction_sat(self):
        z3_script = """
x = Int('x')
y = Int('y')
s = Solver()
s.add(x > 2, y < 10, x + y == 10)
if s.check() == sat:
    print('sat')
    print(s.model())
"""
        receipt = reasoning_service.execute_neurosymbolic_deduction(
            problem_statement="Find integers x > 2 and y < 10 such that x + y = 10",
            z3_code=z3_script
        )
        self.assertEqual(receipt.solver_status, "SAT")
        self.assertTrue(receipt.is_mathematically_proven)
        self.assertIn("sat", receipt.verification_output)

    def test_analogical_mapping_tool_invocation(self):
        res = analogical_mapping_tool.invoke({
            "target_problem": "Circuit breaker design",
            "source_domain": "immune_system",
            "target_domain": "software"
        })
        self.assertIn("entity_mappings", res)


if __name__ == "__main__":
    unittest.main()
