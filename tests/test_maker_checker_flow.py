import pytest
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_maker_checker_flow():
    """
    Tests the End-to-End flow of the Maker-Checker pipeline.
    Validates that:
    1. CEO routes to PM
    2. PM routes to Maker (Prompt Engineer)
    3. Checker (Validator) evaluates it
    """
    
    # Mocking the Orchestration Service directly to avoid real LLM calls
    from src.core.services.orchestration_service import OrchestrationService
    orch = OrchestrationService()
    
    # We will patch the LLM calls in the agents
    with patch("src.agents.factory_ceo.orchestrator.ChatOpenAI") as MockCeoLLM, \
         patch("src.agents.prompt_engineer.orchestrator.ChatOpenAI") as MockMakerLLM, \
         patch("src.agents.agent_validator.orchestrator.ChatOpenAI") as MockCheckerLLM:
             
        # Mock CEO returns saturated
        ceo_llm_instance = MagicMock()
        ceo_llm_instance.invoke.return_value = MagicMock(content="YES")
        MockCeoLLM.return_value = ceo_llm_instance
        
        # Mock Maker returns fake prompt
        maker_llm_instance = MagicMock()
        maker_llm_instance.invoke.return_value = MagicMock(
            dict=lambda: {"system_prompt": "Fake Prompt", "few_shot_examples": []}
        )
        # Handle with_structured_output chaining
        MockMakerLLM.return_value.with_structured_output.return_value = maker_llm_instance
        
        # Mock Checker returns valid on first pass
        checker_llm_instance = MagicMock()
        checker_result = MagicMock()
        checker_result.is_valid = True
        checker_result.feedback = ""
        checker_llm_instance.invoke.return_value = checker_result
        MockCheckerLLM.return_value.with_structured_output.return_value = checker_llm_instance
        
        # Run the flow
        result = await orch.run_factory_graph(user_id="test_user", session_id="test_session", input_data="Build me an agent.")
        
        # Assertions
        assert result["status"] == "success"
        # Verify that Maker was called
        assert maker_llm_instance.invoke.called
        # Verify that Checker was called
        assert checker_llm_instance.invoke.called
