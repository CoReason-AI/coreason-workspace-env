"""
Improvement Service — Autonomous remediation & self-improvement engine.
Consumes AuditReport and TestReceipt traces to refactor prompts, forge missing tools, and patch skills.
"""
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from src.core.services.audit_service import audit_service, AuditReport
from src.core.services.testing_service import testing_service, TestReceipt
from src.core.services.tool_forging_service import tool_forging_service
from src.core.services.skill_service import skill_service

logger = logging.getLogger(__name__)


class ImprovementReceipt(BaseModel):
    target_name: str
    actions_taken: List[str]
    remediated_violations: List[str]
    new_audit_score: float
    status: str = Field(..., description="REMEDIATED, PARTIALLY_REMEDIATED, UNCHANGED")


class ImprovementService:
    """
    Consumes audit and testing failure receipts to autonomously refactor prompts, forge tools, or update skills.
    """

    def improve_agent_artifact(
        self,
        target_name: str,
        content: str,
        audit_report: Optional[AuditReport] = None,
        test_receipt: Optional[TestReceipt] = None,
    ) -> ImprovementReceipt:
        """
        Applies automated remediation actions based on audit violations and test tracebacks.
        """
        logger.info(f"Initiating autonomous improvement for '{target_name}'...")
        actions_taken = []
        remediated_violations = []

        if not audit_report:
            audit_report = audit_service.audit_prompt_or_skill(content, target_name)

        improved_content = content

        for v in audit_report.violations:
            if v.rule_id == "RULE_DETERMINISTIC_MATH":
                # Remediation: Forge missing math tool & inject guidance
                math_tool_code = """
def calculate_vat_tool(amount: float, rate: float = 0.20) -> float:
    \"\"\"Calculates VAT deterministically.\"\"\"
    return amount * rate
"""
                math_test_code = """
def test_calc_vat():
    assert calculate_vat_tool(100.0) == 20.0
"""
                forge_res = tool_forging_service.forge_tool(
                    tool_id=f"{target_name}_vat_tool",
                    name="VAT Calculation Tool",
                    description="Deterministic VAT calculation tool",
                    code=math_tool_code,
                    unit_test_code=math_test_code,
                    tags=["forged", "math"]
                )
                if forge_res["status"] == "success":
                    actions_taken.append(f"Forged deterministic tool '{target_name}_vat_tool'")
                    improved_content += f"\n\n[DETERMINISTIC TOOL GUIDANCE]: Use `{target_name}_vat_tool` for calculations."
                    remediated_violations.append(v.rule_id)

            elif v.rule_id == "RULE_MULTIPLE_CHOICE_INTERROGATION":
                improved_content += "\n\n[MANDATE]: Always use multiple_choice_interrogation with 3 options (A, B, C) + 'Other'."
                actions_taken.append("Injected 3-choice multiple_choice_interrogation mandate")
                remediated_violations.append(v.rule_id)

        # Re-audit post remediation
        post_audit = audit_service.audit_prompt_or_skill(improved_content, target_name)

        status = "REMEDIATED" if post_audit.audit_score >= 90.0 else "PARTIALLY_REMEDIATED"

        return ImprovementReceipt(
            target_name=target_name,
            actions_taken=actions_taken,
            remediated_violations=remediated_violations,
            new_audit_score=post_audit.audit_score,
            status=status,
        )


improvement_service = ImprovementService()
