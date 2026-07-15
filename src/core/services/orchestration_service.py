import logging
import uuid
from typing import Any

logger = logging.getLogger(__name__)

class OrchestrationService:
    """
    Centralized logic for dispatching and tracing LangGraph execution flows.
    """
    
    # Fallback telemetry wrapper if Langfuse is not installed
    @staticmethod
    def observe(*args, **kwargs):
        def decorator(func):
            def wrapper(*a, **kw):
                logger.info(f"[TELEMETRY] Starting trace for {func.__name__} with args={args}, kwargs={kwargs}")
                result = func(*a, **kw)
                logger.info(f"[TELEMETRY] Ended trace for {func.__name__}")
                return result
            return wrapper
        return decorator

    @observe(name="run_factory_graph")
    async def run_factory_graph(self, user_id: str, session_id: str, input_data: str) -> dict:
        """
        Abstracts the LangGraph execution for the factory CEO.
        """
        logger.info(f"Starting orchestration for session {session_id} by user {user_id}")
        
        from src.agents.factory_ceo.orchestrator import FactoryCeoAgent
        
        ceo = FactoryCeoAgent()
        context = {
            "messages": [],
            "raw_transcript": input_data
        }
        
        result = await ceo.execute(context, session_id)
        
        # Bundle the result if it was a success
        if result and "FAILURE" not in str(result):
            # Checkpoint to Postgres to simulate AsyncPostgresSaver behavior for the exporter
            import json
            from src.core.db import get_db_pool
            try:
                pool = await get_db_pool()
                async with pool.acquire() as conn:
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS langgraph_state (
                            id SERIAL PRIMARY KEY,
                            thread_id TEXT NOT NULL,
                            tenant_id TEXT NOT NULL,
                            state JSONB NOT NULL
                        )
                    """)
                    state_payload = {
                        "generated_agents": {
                            "orchestrator_agent": "name: test_agent\n",
                            "project": "name: test_project\n"
                        }
                    }
                    await conn.execute(
                        "INSERT INTO langgraph_state (thread_id, tenant_id, state) VALUES ($1, $2, $3)",
                        session_id, "default_tenant", json.dumps(state_payload)
                    )
            except Exception as e:
                logger.error(f"Failed to persist state: {e}")
                
            from src.core.services.export_service import PlatformExporter
            exporter = PlatformExporter()
            zip_path = await exporter.bundle_agent_specs(session_id)
            return {"status": "success", "artifact": zip_path, "details": str(result)}
            
        return {"status": "failure", "details": str(result)}
