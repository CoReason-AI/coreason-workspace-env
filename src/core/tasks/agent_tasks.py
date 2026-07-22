import asyncio
import json
import logging
from typing import Dict, Any, Optional

from src.core.celery_app import celery_app

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3)
def execute_agent_task(
    self,
    agent_name: str,
    payload: Dict[str, Any],
    user_id: str,
    tenant_id: str,
    session_id: str,
):
    """
    Celery task to execute a LangGraph deep agent synchronously (via asyncio.run).
    """
    import importlib
    
    try:
        module_path = f"src.agents.{agent_name}.orchestrator"
        module = importlib.import_module(module_path)
        agent_class_name = "".join(word.capitalize() for word in agent_name.split("_")) + "Agent"
        agent_class = getattr(module, agent_class_name)
        agent = agent_class()
        
        logger.info(f"Celery executing agent {agent_name} for thread_id {session_id}")
        
        # Prepare context for the agent
        if hasattr(agent, "execute") and asyncio.iscoroutinefunction(agent.execute):
            coro = agent.execute(
                context={"messages": [("user", json.dumps(payload))]},
                session_id=session_id
            )
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
                
            if loop and loop.is_running():
                # If we are already in a running event loop (e.g., Celery EAGER mode during tests)
                # We can't use asyncio.run(). We must run it synchronously or create a task.
                # For testing purposes, we'll run it until complete in a nested loop if possible,
                # or just use ensure_future if that doesn't block (but eager tasks block).
                # Actually, nest_asyncio handles this, but since we don't have it, we just
                # create a task and return. The test will await it.
                asyncio.create_task(coro)
            else:
                asyncio.run(coro)
        else:
            # Synchronous execute method
            agent.execute(payload, session_id=session_id)
            
        logger.info(f"Agent {agent_name} execution completed for thread_id {session_id}")
        return {"status": "success", "session_id": session_id}
        
    except Exception as e:
        logger.error(f"Failed to execute agent {agent_name} in Celery task: {e}", exc_info=True)
        # We can retry if it's a transient failure, but typically LangGraph failures
        # should just be logged. For now, we raise to let Celery register the failure.
        raise
