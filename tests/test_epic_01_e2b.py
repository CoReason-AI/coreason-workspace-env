import os
import pytest
from unittest.mock import MagicMock, patch
from src.agents.agent_validator.orchestrator import AgentValidatorAgent, ValidatorOutput

@patch("src.agents.agent_validator.orchestrator.create_agent")
def test_agent_validator_mocked_e2b(mock_create_agent):
    """
    Unit test to verify the AgentValidatorAgent correctly spins up a react agent
    with the E2B tool and parses the output, without hitting the live API.
    """
    # Setup mock react agent
    mock_react_agent = MagicMock()
    # Simulate the react agent invoking tools and returning a final state
    mock_react_agent.invoke.return_value = {
        "messages": [
            MagicMock(content="I ran the code in the sandbox. It passed.")
        ]
    }
    mock_create_agent.return_value = mock_react_agent
    
    # Initialize the agent
    with patch("src.agents.agent_validator.orchestrator.ChatOpenAI.with_structured_output") as mock_wso:
        # Mock the structured LLM to return a predictable ValidatorOutput
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = ValidatorOutput(is_valid=True, feedback="All good.")
        mock_wso.return_value = mock_structured_llm
        
        agent = AgentValidatorAgent()
        
        # Mock the e2b tool to force the tools loop
        agent.e2b_tool = MagicMock()
        
        result = agent.execute({"data": "test payload"}, session_id="test_123")
    
    # Assert the react agent was called
    mock_create_agent.assert_called_once()
    mock_react_agent.invoke.assert_called_once()
    
    # Assert the final output was correctly parsed
    assert isinstance(result, ValidatorOutput)
    assert result.is_valid is True
    assert result.feedback == "All good."

@pytest.mark.skipif(not os.getenv("E2B_API_KEY"), reason="E2B_API_KEY not set in environment.")
def test_agent_validator_live_e2b():
    """
    Live integration test to verify the E2B tool works in the AgentValidatorAgent.
    """
    agent = AgentValidatorAgent()
    
    # This payload should force the LLM to use the E2BDataAnalysisTool
    payload = "Please write a python script that prints 'hello world' and run it in the E2B sandbox. Return the result."
    
    result = agent.execute({"data": payload}, session_id="test_live_123")
    
    assert isinstance(result, ValidatorOutput)

@pytest.mark.skipif(not os.getenv("E2B_API_KEY"), reason="E2B_API_KEY not set in environment.")
def test_e2b_security_isolation():
    """
    Live security test to ensure E2B microVM prevents host OS access.
    """
    agent = AgentValidatorAgent()
    
    payload = "Write and execute a python script that lists the root directory '/' using os.listdir. Return the results."
    
    result = agent.execute({"data": payload}, session_id="test_security_123")
    
    assert isinstance(result, ValidatorOutput)
    # The output should not contain the actual host OS files (like '.env' or 'src')
    assert "pyproject.toml" not in result.feedback
