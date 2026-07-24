"""
Causal Proving & Thought Structuring Tools — Exposes CausalProvingService and ThoughtStructuringService to LangGraph agents.
"""
from typing import Dict, Any, List, Optional
from langchain_core.tools import tool

from src.core.services.causal_proving_service import causal_proving_service
from src.core.services.thought_structuring_service import thought_structuring_service


@tool
def prove_causal_hypothesis_tool(
    hypothesis: str,
    treatment: str,
    outcome: str,
    confounders: List[str],
) -> Dict[str, Any]:
    """
    Builds a causal DAG (DoWhy framework), computes do-intervention Average Treatment Effect (ATE),
    and evaluates Bradford Hill epidemiological criteria to mathematically prove or disprove a causal hypothesis.
    """
    receipt = causal_proving_service.prove_causal_hypothesis(
        hypothesis=hypothesis,
        treatment=treatment,
        outcome=outcome,
        confounders=confounders,
    )
    return receipt.model_dump()


@tool
def organize_thoughts_tool(raw_unorganized_text: str) -> Dict[str, Any]:
    """
    Takes unorganized, raw brainstorming notes or high-entropy thoughts and parses them
    into a clean, structured MECE hierarchy with priorities and categories.
    """
    artifact = thought_structuring_service.organize_unorganized_thoughts(raw_unorganized_text)
    return artifact.model_dump()


@tool
def structure_complex_thoughts_tool(complex_concept: str) -> Dict[str, Any]:
    """
    Decomposes complex ideas into a structured Tree-of-Thoughts / Chain-of-Knowledge graph.
    """
    return thought_structuring_service.structure_complex_thoughts(complex_concept)
