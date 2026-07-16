import pytest
import uuid
import json
from langchain_core.messages import HumanMessage, AIMessage

from src.core.evaluation.eval_config import get_eval_client, correct_answer_evaluator

class DummyAgent:
    """A dummy agent used for isolated testing of the simulated user harness."""
    def __init__(self):
        self.conversation = []

    def respond(self, message: str) -> str:
        self.conversation.append(HumanMessage(content=message))
        
        # Simple simulated logic
        response = ""
        if "inventory" in message.lower():
            response = "I will help you build an inventory management agent. What are your specific requirements?"
        elif "barcode" in message.lower():
            response = "I have added barcode scanning to the requirements."
        else:
            response = "Can you clarify your request?"
            
        self.conversation.append(AIMessage(content=response))
        return response

class SimulatedUser:
    """A simulated user that tests an agent's conversational capabilities."""
    def __init__(self, agent, scenario: list):
        self.agent = agent
        self.scenario = scenario
        self.trajectory = []
        
    def run(self):
        for user_msg in self.scenario:
            self.trajectory.append({"role": "user", "content": user_msg})
            agent_response = self.agent.respond(user_msg)
            self.trajectory.append({"role": "assistant", "content": agent_response})
            
        return self.trajectory


@pytest.mark.asyncio
async def test_simulated_user_trajectory():
    """
    Tests that a Simulated User can interact with an agent and that the
    resulting trajectory can be evaluated.
    """
    agent = DummyAgent()
    
    scenario = [
        "I need an inventory management agent.",
        "It must support barcode scanning."
    ]
    
    sim_user = SimulatedUser(agent=agent, scenario=scenario)
    trajectory = sim_user.run()
    
    # Assert trajectory length (2 turns = 4 messages)
    assert len(trajectory) == 4
    
    # Assert expected interactions
    assert "inventory management agent" in trajectory[1]["content"].lower()
    assert "barcode scanning" in trajectory[3]["content"].lower()
    
    # Here we would normally push the trajectory to LangSmith for full LLM-as-a-judge scoring
    client = get_eval_client()
    
    # Dummy mock run to verify eval wrapper logic
    class MockRun:
        def __init__(self):
            self.outputs = {"output": trajectory[-1]["content"]}
            
    class MockExample:
        def __init__(self):
            self.outputs = {"expected": "I have added barcode scanning to the requirements."}
            
    score_result = correct_answer_evaluator(MockRun(), MockExample())
    assert score_result["score"] == 1.0
