"""
Audit Service — Deterministic static analysis & rule-based auditing of agent prompts, skills, and manifests.
Follows the principle: Deterministic checks (AST, regex, math calculations, schema purity) use Python tools;
never rely on probabilistic LLM output for static verification.
"""
import re
import ast
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from src.core.services.skill_service import skill_service

logger = logging.getLogger(__name__)


class AuditViolation(BaseModel):
    rule_id: str
    severity: str = Field(..., description="CRITICAL, HIGH, MEDIUM, LOW")
    category: str
    message: str
    remediation_suggestion: str


class AuditReport(BaseModel):
    target_name: str
    target_type: str = Field(..., description="prompt, skill, agent_manifest, python_tool")
    audit_score: float = Field(..., description="Score between 0.0 and 100.0")
    status: str = Field(..., description="PASSED, NEEDS_IMPROVEMENT, FAILED")
    violations: List[AuditViolation] = Field(default_factory=list)
    rules_applied: List[str] = Field(default_factory=list)


class AuditService:
    """
    Performs deterministic auditing of agent system prompts, markdown skills, python code, and YAML manifests.
    """

    def audit_prompt_or_skill(self, content: str, target_name: str, target_type: str = "prompt") -> AuditReport:
        """
        Audits a system prompt or markdown skill against deterministic rules.
        """
        logger.info(f"Auditing {target_type} '{target_name}' deterministically...")
        violations: List[AuditViolation] = []
        rules_applied = [
            "deterministic_tool_usage.md",
            "prompt_injection_security.md",
            "schema_purity_check.md"
        ]

        # 1. Deterministic Rule Check: Probabilistic Math / Calculation Anti-Pattern
        math_keywords = ["calculate tax", "compute vat", "add numbers", "multiply rate", "divide total", "do math", "calculate numbers", "calculate amount"]
        for kw in math_keywords:
            if kw in content.lower():
                violations.append(AuditViolation(
                    rule_id="RULE_DETERMINISTIC_MATH",
                    severity="HIGH",
                    category="anti_pattern",
                    message=f"Prompt contains text asking for manual math calculation ('{kw}'). Probabilistic LLMs must not perform calculations.",
                    remediation_suggestion="Delegate arithmetic or calculations to a deterministic python tool (e.g., calculate_vat_tool)."
                ))

        # 2. Deterministic Rule Check: Raw Hardcoded Credentials / API Keys
        if re.search(r'(sk-[a-zA-Z0-9]{20,}|bearer\s+[a-zA-Z0-9_\-\.]{20,}|password\s*=\s*[\'"][^\'"]+[\'"])', content, re.IGNORECASE):
            violations.append(AuditViolation(
                rule_id="RULE_NO_HARDCODED_SECRETS",
                severity="CRITICAL",
                category="security",
                message="Hardcoded API keys or credentials detected in prompt/skill context.",
                remediation_suggestion="Inject secrets dynamically from HashiCorp Vault or environment variables."
            ))

        # 3. Deterministic Rule Check: Open-ended Interrogation Anti-Pattern
        if "ask the user whatever they want" in content.lower() or "open-ended questions" in content.lower():
             violations.append(AuditViolation(
                rule_id="RULE_MULTIPLE_CHOICE_INTERROGATION",
                severity="MEDIUM",
                category="context_engineering",
                message="Open-ended human interrogation detected. Violates DeepAgent 3-choice multiple choice rule.",
                remediation_suggestion="Use multiple_choice_interrogation skill with 3 concrete options (A, B, C) + 'Other'."
            ))

        # Score calculation
        deductions = sum(30 if v.severity == "CRITICAL" else 15 if v.severity == "HIGH" else 5 for v in violations)
        score = max(0.0, 100.0 - deductions)
        status = "PASSED" if score >= 90.0 else "NEEDS_IMPROVEMENT" if score >= 60.0 else "FAILED"

        return AuditReport(
            target_name=target_name,
            target_type=target_type,
            audit_score=score,
            status=status,
            violations=violations,
            rules_applied=rules_applied
        )

    def audit_python_tool(self, code: str, tool_name: str) -> AuditReport:
        """
        Deterministically audits Python tool code using Python AST.
        """
        violations: List[AuditViolation] = []
        rules_applied = ["python_ast_check", "exception_handling_check"]

        try:
            tree = ast.parse(code)
            # Check for bare except: blocks
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    violations.append(AuditViolation(
                        rule_id="RULE_NO_BARE_EXCEPT",
                        severity="HIGH",
                        category="code_quality",
                        message="Bare 'except:' handler detected in python tool.",
                        remediation_suggestion="Specify explicit exception types (e.g., except ValueError as e:)."
                    ))
        except SyntaxError as e:
            violations.append(AuditViolation(
                rule_id="RULE_SYNTAX_ERROR",
                severity="CRITICAL",
                category="syntax",
                message=f"Python syntax error: {str(e)}",
                remediation_suggestion="Fix Python syntax error."
            ))

        deductions = sum(30 if v.severity == "CRITICAL" else 15 if v.severity == "HIGH" else 5 for v in violations)
        score = max(0.0, 100.0 - deductions)
        status = "PASSED" if score >= 90.0 else "NEEDS_IMPROVEMENT" if score >= 60.0 else "FAILED"

        return AuditReport(
            target_name=tool_name,
            target_type="python_tool",
            audit_score=score,
            status=status,
            violations=violations,
            rules_applied=rules_applied
        )


audit_service = AuditService()
