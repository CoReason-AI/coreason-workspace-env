import pytest
from pydantic import BaseModel, ValidationError
from src.core.ontology import CognitiveDeliberativeEnvelopeState

class MockPayload(BaseModel):
    name: str

def test_envelope_fsm_token_limit():
    # Test valid envelope
    valid_env = CognitiveDeliberativeEnvelopeState[MockPayload](
        deliberation_trace="This is a short trace.",
        payload=MockPayload(name="test")
    )
    assert valid_env.payload.name == "test"
    
    # In src.core.ontology, CognitiveDeliberativeEnvelopeState uses Annotated[str, StringConstraints(max_length=...)]
    # We should ensure that an extraordinarily long string fails validation
    long_trace = "A" * 150000  # Assume FSM limit is well below 150000
    with pytest.raises(ValidationError):
        CognitiveDeliberativeEnvelopeState[MockPayload](
            deliberation_trace=long_trace,
            payload=MockPayload(name="test")
        )
