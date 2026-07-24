import unittest
from src.core.services.tool_forging_service import tool_forging_service


class TestToolForgingService(unittest.TestCase):
    def test_forge_tool_success(self):
        tool_code = """
def calculate_vat(amount: float, rate: float = 0.20) -> float:
    return amount * rate
"""
        unit_test_code = """
def test_vat():
    assert calculate_vat(100.0) == 20.0
    assert calculate_vat(200.0, 0.10) == 20.0
"""
        res = tool_forging_service.forge_tool(
            tool_id="test_vat_calc",
            name="VAT Calculator Tool",
            description="Calculates VAT for transactions",
            code=tool_code,
            unit_test_code=unit_test_code,
            tags=["finance", "tax"]
        )

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["tool"]["tool_id"], "test_vat_calc")
        self.assertIn("urn:oid:1.3.6.1.4.1.66197:tool:test_vat_calc", res["tool"]["urn"])

        # Discovery test
        discovered = tool_forging_service.list_forged_tools(query="VAT")
        self.assertTrue(len(discovered) >= 1)

    def test_forge_tool_validation_failure(self):
        tool_code = """
def broken_tool():
    return 1 / 0
"""
        unit_test_code = """
def test_broken():
    assert broken_tool() == 42
"""
        res = tool_forging_service.forge_tool(
            tool_id="broken_tool_id",
            name="Broken Tool",
            description="Fails unit tests",
            code=tool_code,
            unit_test_code=unit_test_code
        )

        self.assertEqual(res["status"], "error")
        self.assertIn("Maker-Checker validation gate", res["message"])


if __name__ == "__main__":
    unittest.main()
