import pytest
import os
import uuid
from typing import Dict, Any

from src.core.evaluation.eval_config import dialectical_synthesis_evaluator, get_eval_client

# Dummy run and example classes for evaluation mock
class MockRun:
    def __init__(self, outputs: Dict[str, Any]):
        self.outputs = outputs

class MockExample:
    def __init__(self, inputs: Dict[str, Any] = None, outputs: Dict[str, Any] = None):
        self.inputs = inputs or {}
        self.outputs = outputs or {}


@pytest.mark.asyncio
async def test_dialectical_synthesis_positive():
    """
    Evaluates a generated payload that successfully employs Dialectical Synthesis.
    """
    good_payload = """
    Thesis: We should build the system as a monolithic architecture for speed of delivery.
    Antithesis: However, a monolithic architecture will create a single point of failure and hinder scaling.
    Synthesis: We will build a modular monolith, allowing fast delivery but bounded contexts for future microservices.
    """
    
    run = MockRun(outputs={"output": good_payload})
    example = MockExample()
    
    result = dialectical_synthesis_evaluator(run, example)
    assert result["score"] == 1.0


@pytest.mark.asyncio
async def test_dialectical_synthesis_negative():
    """
    Evaluates a payload that fails to employ Dialectical Synthesis.
    """
    bad_payload = """
    We should just build a microservice architecture right away because it scales better.
    """
    
    run = MockRun(outputs={"output": bad_payload})
    example = MockExample()
    
    result = dialectical_synthesis_evaluator(run, example)
    assert result["score"] == 0.0
