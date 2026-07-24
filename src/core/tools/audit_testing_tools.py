"""
Audit, Testing & Autonomous Improvement Tools — Parity with Claude Code & Antigravity Checker Loops.
Exposes AuditService, TestingService, and ImprovementService to LangGraph agents.
"""
from typing import Dict, Any, Optional
from langchain_core.tools import tool

from src.core.services.audit_service import audit_service
from src.core.services.testing_service import testing_service
from src.core.services.improvement_service import improvement_service


@tool
def audit_artifact_tool(target_name: str, content: str, target_type: str = "prompt") -> Dict[str, Any]:
    """
    Deterministically audits a system prompt, skill, or python tool for anti-patterns,
    un-sanitized inputs, or manual math calculations.
    """
    report = audit_service.audit_prompt_or_skill(content, target_name, target_type)
    return report.model_dump()


@tool
def run_agent_tests_tool(agent_name: str, test_code: str, agent_code: str) -> Dict[str, Any]:
    """
    Executes automated unit tests against an agent graph inside an isolated OpenShell sandbox.
    """
    receipt = testing_service.run_agent_test_suite(agent_name, test_code, agent_code)
    return receipt.model_dump()


@tool
def improve_artifact_tool(target_name: str, content: str) -> Dict[str, Any]:
    """
    Autonomously remediates audit violations and test failures by forging missing deterministic tools
    and refactoring prompts.
    """
    receipt = improvement_service.improve_agent_artifact(target_name, content)
    return receipt.model_dump()
