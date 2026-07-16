import asyncio
import os
import unittest
from unittest.mock import AsyncMock, patch

os.environ["OPENAI_API_KEY"] = "test_mock_key"

from src.core.tools.evaluator import evaluate_artifact
from src.core.ontology import EvaluationScore
from src.core.engine.approver_node import approver_node

class TestEvaluatorAndApprover(unittest.IsolatedAsyncioTestCase):
    
    @patch('src.core.tools.evaluator._run_evaluation', new_callable=AsyncMock)
    async def test_evaluate_artifact_consensus_pass(self, mock_run_eval):
        # Mock the internal evaluation to return a passing score
        mock_run_eval.return_value = EvaluationScore(
            score=0.9,
            reasoning="Perfect code"
        )
        
        result = await evaluate_artifact.ainvoke({
            "user_prompt": "Make a function",
            "generated_code": "def func(): pass",
            "session_id": "test-session"
        })
        
        self.assertIn("EVALUATION PASSED", result)
        self.assertIn("0.9", result)
        self.assertEqual(mock_run_eval.call_count, 2)  # Two models for consensus

    @patch('src.core.engine.approver_node.init_chat_model')
    async def test_approver_node_dialectical_synthesis(self, mock_init_chat_model):
        
        # Mock the LLM that generates the Dialectical Synthesis
        mock_llm_instance = mock_init_chat_model.return_value
        
        class MockResponse:
            content = "THESIS: ...\nANTITHESIS: ...\nSYNTHESIS: ..."
            
        mock_llm_instance.ainvoke = AsyncMock(return_value=MockResponse())
        
        state = {
            "user_prompt": "Do X",
            "generated_code": "def bad(): pass",
            "thread_id": "session-123"
        }
        
        # Patching ainvoke directly on the tool fails on teardown due to Pydantic constraints.
        # So we temporarily replace the tool's arun method for the test.
        with patch.object(evaluate_artifact, '_arun', new=AsyncMock(return_value="EVALUATION FAILED. Consensus Score: 0.2")):
            result = await approver_node(state)
        
        self.assertEqual(result["status"], "REJECTED")
        self.assertIn("THESIS:", result["approver_feedback"])
        self.assertIn("SYNTHESIS:", result["approver_feedback"])

if __name__ == '__main__':
    unittest.main()
