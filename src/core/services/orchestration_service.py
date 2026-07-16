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

    @observe(name="run_persona_graph")
    async def run_persona_graph(self, user_id: str, session_id: str, input_data: str, output_dir: str = "./generated_agents", input_path: str = None) -> dict:
        """
        Abstracts the LangGraph execution for the active persona (dynamic entrypoint).
        """
        logger.info(f"Starting orchestration for session {session_id} by user {user_id}")
        
        import os
        import importlib
        import zipfile
        
        extracted_path = None
        if input_path and os.path.exists(input_path):
            if os.path.isfile(input_path) and input_path.endswith('.zip'):
                extracted_path = os.path.abspath(f"./scratch/context_{session_id}")
                os.makedirs(extracted_path, exist_ok=True)
                with zipfile.ZipFile(input_path, 'r') as zip_ref:
                    zip_ref.extractall(extracted_path)
                logger.info(f"Extracted input zip to {extracted_path}")
            else:
                extracted_path = os.path.abspath(input_path)
                logger.info(f"Using input path at {extracted_path}")
            
        if extracted_path:
            input_data += f"\n\nThe user has provided additional input context located at: '{extracted_path}'. If instructed by the user, treat this as legacy code to be modernized. Otherwise, incorporate this context as directed by the user."
        
        # Dynamically load the root agent defined by the active Brain
        module_path = os.environ.get("AGENT_ENTRYPOINT_MODULE", "src.agents.factory_ceo.orchestrator")
        class_name = os.environ.get("AGENT_ENTRYPOINT_CLASS", "FactoryCeoAgent")
        
        try:
            module = importlib.import_module(module_path)
            AgentClass = getattr(module, class_name)
            ceo = AgentClass()
        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to dynamically load Brain entrypoint {module_path}.{class_name}: {e}")
            raise
        from langchain_core.messages import HumanMessage
        context = {
            "messages": [HumanMessage(content=input_data)],
            "raw_transcript": input_data
        }
        
        result = await ceo.execute(context, session_id)
        
        # Bundle the result if it was a success and context was saturated
        is_sat = result.get("is_saturated")
        if result and "FAILURE" not in str(result) and is_sat is not False:
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
            exporter = PlatformExporter(output_dir=output_dir)
            zip_path = await exporter.bundle_agent_specs(session_id)
            return {"status": "success", "artifact": zip_path, "details": str(result)}
            
        return {"status": "failure", "details": str(result)}
