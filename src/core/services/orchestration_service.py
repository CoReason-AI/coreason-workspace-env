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
            from src.core.services.export_service import PlatformExporter
            exporter = PlatformExporter()
            zip_path = await exporter.bundle_agent_specs(session_id)
            return {"status": "success", "artifact": zip_path, "details": str(result)}
            
        return {"status": "failure", "details": str(result)}
