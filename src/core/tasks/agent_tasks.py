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
    Captures OpenTelemetry / TraceService spans for full observability and meta-programming.
    """
    import importlib
    import time
    from src.core.services.trace_service import trace_service

    start_t = time.time()
    trace_service.start_trace(
        job_id=session_id,
        agent_name=agent_name,
        user_id=user_id,
        tenant_id=tenant_id,
        metadata={"payload": payload}
    )

    try:
        module_path = f"src.agents.{agent_name}.orchestrator"
        module = importlib.import_module(module_path)
        agent_class_name = "".join(word.capitalize() for word in agent_name.split("_")) + "Agent"
        agent_class = getattr(module, agent_class_name)
        agent = agent_class()
        
        logger.info(f"Celery executing agent {agent_name} for thread_id {session_id}")
        trace_service.add_step_summary(session_id, f"Instantiated agent orchestrator {agent_class_name}")
        
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
                asyncio.create_task(coro)
            else:
                asyncio.run(coro)
        else:
            # Synchronous execute method
            agent.execute(payload, session_id=session_id)
            
        end_t = time.time()
        trace_service.add_span(
            job_id=session_id,
            name=f"execute_{agent_name}",
            span_type="agent_step",
            start_time=start_t,
            end_time=end_t,
            input_data=payload,
            output_data={"status": "completed"}
        )
        trace_service.finish_trace(session_id, status="success")
        logger.info(f"Agent {agent_name} execution completed for thread_id {session_id}")
        return {"status": "success", "session_id": session_id}
        
    except Exception as e:
        end_t = time.time()
        trace_service.add_span(
            job_id=session_id,
            name=f"execute_{agent_name}",
            span_type="agent_step",
            start_time=start_t,
            end_time=end_t,
            input_data=payload,
            error=str(e)
        )
        trace_service.finish_trace(session_id, status="error", error=str(e))
        logger.error(f"Failed to execute agent {agent_name} in Celery task: {e}", exc_info=True)
        raise
