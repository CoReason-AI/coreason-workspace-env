"""
Reasoning Tools — Analogical Structure Mapping & Neuro-Symbolic Z3 Deduction Tools.
Exposes ReasoningService to LangGraph agents.
"""
from typing import Dict, Any, Optional
from langchain_core.tools import tool

from src.core.services.reasoning_service import reasoning_service


@tool
def analogical_mapping_tool(
    target_problem: str,
    source_domain: str = "biological_ecosystems",
    target_domain: str = "distributed_cloud_architecture",
) -> Dict[str, Any]:
    """
    Performs Structure Mapping Theory (Gentner SMT) by constructing explicit relational mappings
    between a source domain exemplar and a target domain problem.
    """
    artifact = reasoning_service.perform_analogical_structure_mapping(
        target_problem=target_problem,
        source_domain=source_domain,
        target_domain=target_domain,
    )
    return artifact.model_dump()


@tool
def neurosymbolic_deduction_tool(
    problem_statement: str,
    z3_code: str,
) -> Dict[str, Any]:
    """
    Executes a neuro-symbolic deduction loop using Python Z3 SMT solver.
    Solves constraints deterministically to provide mathematical proof.
    """
    receipt = reasoning_service.execute_neurosymbolic_deduction(
        problem_statement=problem_statement,
        z3_code=z3_code,
    )
    return receipt.model_dump()
