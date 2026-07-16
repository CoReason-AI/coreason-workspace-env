"""
Evaluation Configuration.
Sets up the LangSmith client to intercept telemetry and test results locally,
avoiding any cloud transmission.
"""
import os
from langsmith import Client

# Force the LangSmith endpoint to our local interceptor (e.g. Harbor)
os.environ["LANGCHAIN_ENDPOINT"] = "http://localhost:1984"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "local"
os.environ["LANGCHAIN_PROJECT"] = "coreason-evals"

# Global eval client
eval_client = Client(
    api_url="http://localhost:1984",
    api_key="local"
)

def get_eval_client() -> Client:
    """Returns a LangSmith Client explicitly configured for local data sovereignty."""
    return eval_client

# Define standard evaluator wrappers here
def correct_answer_evaluator(run, example):
    """
    LLM-as-a-judge for answer correctness.
    To be wired into deepagents-evals or native langchain evals.
    """
    from langchain_openai import ChatOpenAI
    # In a real scenario, this would use a complex prompt to judge correctness.
    # For now, we return a mock score or simple check.
    score = 1.0 if run.outputs.get("output") == example.outputs.get("expected") else 0.0
    return {"key": "correctness", "score": score}

def dialectical_synthesis_evaluator(run, example):
    """
    Evaluates whether the agent trajectory contains Thesis/Antithesis/Synthesis.
    """
    output = run.outputs.get("output", "")
    
    has_thesis = "thesis" in output.lower()
    has_antithesis = "antithesis" in output.lower() or "counter" in output.lower()
    has_synthesis = "synthesis" in output.lower() or "reconcil" in output.lower()
    
    score = 1.0 if (has_thesis and has_antithesis and has_synthesis) else 0.0
    return {"key": "dialectical_synthesis", "score": score}
