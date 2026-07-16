"""
Native LCEL Evaluator Tool (Multi-Model Consensus)

This module replaces third-party wrappers (like Ragas) with native
LangChain v1 Expression Language (LCEL) pipelines to semantically score
artifacts. It enforces explicit prompt templates and multi-model consensus
to adhere to strict GxP governance guidelines.
"""

import asyncio
from typing import Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field

# We use the existing observability service to push scores to Langfuse
from src.core.services.observability_service import ObservabilityService
from src.core.ontology import EvaluationScore, EvaluateArtifactRequest


# Explicit, transparent prompt template (No black-box load_evaluator)
EVALUATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are an expert, strict code evaluator. You must assess the provided code against the user's original request. Determine if the code correctly and completely fulfills the request. Provide a score between 0.0 and 1.0, where 1.0 is a perfect solution."),
    ("user", "User Request:\n{user_prompt}\n\nGenerated Code:\n{generated_code}")
])


async def _run_evaluation(llm, user_prompt: str, generated_code: str) -> EvaluationScore:
    """Runs a single LCEL evaluation pipeline."""
    # LCEL pipeline: Prompt -> LLM (forced to output ScoreSchema)
    pipeline = EVALUATION_PROMPT | llm.with_structured_output(EvaluationScore)
    
    result = await pipeline.ainvoke({
        "user_prompt": user_prompt,
        "generated_code": generated_code
    })
    return result


@tool(args_schema=EvaluateArtifactRequest)
async def evaluate_artifact(user_prompt: str, generated_code: str, session_id: str) -> str:
    """
    Semantically evaluates an artifact using Multi-Model Consensus.
    It runs the evaluation twice (simulating a heterogeneous judge panel)
    and pushes the consensus score natively to Langfuse.
    """
    # Initialize our heterogeneous consensus models.
    # In a true multi-model setup, this would be gpt-4o and claude-3-5-sonnet.
    # Here we mock consensus by using two distinct temperature profiles.
    judge_a = init_chat_model(model="gpt-4o", model_provider="openai", temperature=0.0)
    judge_b = init_chat_model(model="gpt-4o", model_provider="openai", temperature=0.5)

    # Run consensus models concurrently
    results = await asyncio.gather(
        _run_evaluation(judge_a, user_prompt, generated_code),
        _run_evaluation(judge_b, user_prompt, generated_code)
    )
    
    score_a = results[0].score
    score_b = results[1].score
    
    # Calculate consensus
    consensus_score = (score_a + score_b) / 2.0
    
    # Log to Langfuse natively
    obs_service = ObservabilityService()
    if obs_service.langfuse_public and obs_service.langfuse_secret:
        try:
            from langfuse import Langfuse
            langfuse = Langfuse(
                public_key=obs_service.langfuse_public,
                secret_key=obs_service.langfuse_secret,
                host=obs_service.langfuse_host
            )
            langfuse.score(
                trace_id=session_id,
                name="semantic_consensus_score",
                value=consensus_score,
                comment=f"Judge A: {score_a}, Judge B: {score_b}"
            )
            langfuse.flush()
        except ImportError:
            pass # langfuse not installed in this environment
            
    # Format the return result for the Approver Agent
    if consensus_score >= 0.8:
        return f"EVALUATION PASSED. Consensus Score: {consensus_score}\nJudge A Reasoning: {results[0].reasoning}\nJudge B Reasoning: {results[1].reasoning}"
    else:
        return f"EVALUATION FAILED. Consensus Score: {consensus_score}\nJudge A Reasoning: {results[0].reasoning}\nJudge B Reasoning: {results[1].reasoning}"
