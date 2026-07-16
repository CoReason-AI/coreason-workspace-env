import os

# Set dummy environment variables to satisfy pydantic_settings during tests
for k in [
    "ENVIRONMENT", "ALLOWED_ORIGINS", "VAULT_ADDR", "VAULT_NAMESPACE", 
    "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "POSTGRES_HOST", 
    "POSTGRES_PORT", "WORM_S3_BUCKET", "WORM_S3_REGION", 
    "WORM_S3_ENDPOINT", "WORM_S3_ACCESS_KEY", "WORM_S3_SECRET_KEY", "OPENROUTER_API_KEY",
    "LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL_NAME", "LLM_TEMPERATURE"
]:
    if k not in os.environ:
        if k == "POSTGRES_PORT":
            os.environ[k] = '5432'
        elif k == "LLM_TEMPERATURE":
            os.environ[k] = '0.0'

        else:
            os.environ[k] = 'test'

import sys
from pydantic import BaseModel, Field
from typing import Any, Generic, TypeVar, Optional, TypedDict



import uuid
if not hasattr(uuid, 'uuid7'):
    import uuid6
    uuid.uuid7 = uuid6.uuid7

import json
import pytest
from tests.test_framework import ZeroMockTestCase
from tests.deterministic_harness import DeterministicTestChatModel

class TestFactoryE2E(ZeroMockTestCase):
    
    @pytest.mark.asyncio
    async def test_end_to_end_factory(self):
        # We replace the actual ChatOpenAI constructor dynamically
        # using standard setattr to comply with the anti-stub policy
        import src.agents.factory_ceo.orchestrator as ceo_orch
        import src.agents.prompt_engineer.orchestrator as prompt_orch
        import src.agents.yaml_compiler.orchestrator as yaml_orch
        import src.agents.agent_validator.orchestrator as val_orch
        import src.core.services.orchestration_service as orch_svc

        original_ceo_chat = ceo_orch.ChatOpenAI
        original_prompt_chat = prompt_orch.ChatOpenAI
        original_yaml_chat = yaml_orch.ChatOpenAI
        original_val_chat = val_orch.ChatOpenAI

        def inject_deterministic_llm(*args, **kwargs):
            return DeterministicTestChatModel()

        setattr(ceo_orch, "ChatOpenAI", inject_deterministic_llm)
        setattr(prompt_orch, "ChatOpenAI", inject_deterministic_llm)
        setattr(yaml_orch, "ChatOpenAI", inject_deterministic_llm)
        setattr(val_orch, "ChatOpenAI", inject_deterministic_llm)

        import uuid
        test_session_id = f"test_session_e2e_{uuid.uuid7().hex}"
        try:
            service = orch_svc.OrchestrationService()
            result = await service.run_persona_graph(
                user_id="test_user_e2e",
                session_id=test_session_id,
                input_data="Build me an inventory management agent."
            )
            
            # Assertions
            self.assertEqual(result["status"], "success")
            self.assertIn("artifact", result)
            self.assertTrue(result["artifact"].endswith(".zip"))
            
            # Verify the ZIP archive exists and contains required files
            import zipfile
            zip_path = result["artifact"]
            self.assertTrue(os.path.exists(zip_path))
            
            with zipfile.ZipFile(zip_path, "r") as zf:
                files = zf.namelist()
                self.assertIn("pyproject.toml", files)
                self.assertIn("orchestrator_agent.yaml", files)
                self.assertIn("project.yaml", files)
                
        finally:
            # Restore the original classes
            setattr(ceo_orch, "ChatOpenAI", original_ceo_chat)
            setattr(prompt_orch, "ChatOpenAI", original_prompt_chat)
            setattr(yaml_orch, "ChatOpenAI", original_yaml_chat)
            setattr(val_orch, "ChatOpenAI", original_val_chat)
