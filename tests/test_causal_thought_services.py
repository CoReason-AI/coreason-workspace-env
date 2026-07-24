import unittest
from src.core.services.causal_proving_service import causal_proving_service
from src.core.services.thought_structuring_service import thought_structuring_service
from src.core.tools.causal_thought_tools import (
    prove_causal_hypothesis_tool,
    organize_thoughts_tool,
    structure_complex_thoughts_tool,
)


class TestCausalThoughtServices(unittest.TestCase):
    def test_prove_causal_hypothesis(self):
        data = {
            "rate_limiting": [1.0, 2.0, 3.0, 4.0, 5.0],
            "server_latency": [10.0, 8.0, 6.0, 4.0, 2.0],
        }
        receipt = causal_proving_service.prove_causal_hypothesis(
            hypothesis="Rate limiting reduces server latency under load",
            treatment="rate_limiting",
            outcome="server_latency",
            confounders=["concurrent_users"],
            observational_data=data
        )
        self.assertEqual(receipt.treatment, "rate_limiting")
        self.assertTrue(receipt.is_theory_proven)
        self.assertLess(receipt.average_treatment_effect_estimate, 0)  # Inverse relationship

    def test_organize_unorganized_thoughts(self):
        raw_text = """
- We need to design a microservice architecture for state sync
- Run automated unit tests in an isolated sandbox
- Enforce strict security clearance and zero trust policies
"""
        artifact = thought_structuring_service.organize_unorganized_thoughts(raw_text)
        self.assertEqual(len(artifact.structured_groups), 3)
        self.assertEqual(artifact.mece_coverage_score, 100.0)

    def test_causal_thought_tools(self):
        res_proof = prove_causal_hypothesis_tool.invoke({
            "hypothesis": "Unit testing prevents production bugs",
            "treatment": "unit_testing",
            "outcome": "production_bugs",
            "confounders": ["code_complexity"]
        })
        self.assertIn("proof_id", res_proof)

        res_org = organize_thoughts_tool.invoke({
            "raw_unorganized_text": "System design notes and execution steps"
        })
        self.assertIn("structured_groups", res_org)


if __name__ == "__main__":
    unittest.main()
