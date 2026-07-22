import os
import pytest
import asyncio
from unittest.mock import MagicMock, patch

from src.core.celery_app import celery_app
from src.core.tasks.agent_tasks import execute_agent_task

celery_app.conf.update(
    task_always_eager=True,
    task_eager_propagates=True,
)

def test_celery_app_initialization():
    assert celery_app.main == "coreason_tasks"

@pytest.mark.asyncio
async def test_execute_agent_task_success():
    import sys, types
    dummy_module = types.ModuleType("src.agents.mock_task_agent.orchestrator")
    
    dummy_instance = MagicMock()
    async def mock_execute(context=None, session_id=None):
        return {"status": "completed"}
    
    dummy_instance.execute = mock_execute
    dummy_cls = MagicMock(return_value=dummy_instance)
    dummy_module.MockTaskAgentAgent = dummy_cls
    
    sys.modules["src.agents.mock_task_agent.orchestrator"] = dummy_module
    
    res = execute_agent_task.delay(
        agent_name="mock_task_agent",
        payload={"query": "hello"},
        user_id="usr_123",
        tenant_id="tnt_123",
        session_id="job_789"
    )
    
    # Wait briefly for eager loop schedule
    await asyncio.sleep(0.1)
    assert res.status in ("SUCCESS", "PENDING")
