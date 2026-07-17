import logging
import uuid
from typing import Any

logger = logging.getLogger(__name__)

class OrchestrationService:
    """
    Centralized logic for dispatching and tracing LangGraph execution flows.
    """
    
    async def run_persona_graph(self, user_id: str, session_id: str, input_data: str, output_dir: str = "./generated_agents", input_path: str = None) -> dict:
        """
        Abstracts the LangGraph execution for the active persona (dynamic entrypoint).
        """
        logger.info(f"Starting orchestration for session {session_id} by user {user_id}")
        
        is_goal_mode = False
        if input_data.strip().startswith("/goal"):
            is_goal_mode = True
            input_data = input_data.replace("/goal", "", 1).strip()
            logger.info("Goal mode activated: Interrogation disabled.")
        
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
            input_data += f"\n\nThe user has provided an additional context path located at: '{extracted_path}'. Use your tools to read and extract this context if needed."
        
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
            "raw_transcript": input_data,
            "is_goal_mode": is_goal_mode
        }
        result = await ceo.execute(context, session_id)
        
        # Check if the agent is asking a clarifying question (tool call)
        messages = result.get("messages", [])
        is_interactive = False
        interrogation_question = None
        
        interrupts = result.get("__interrupt__", [])
        for interrupt in interrupts:
            val = interrupt.value if hasattr(interrupt, "value") else interrupt
            if isinstance(val, dict) and "action_requests" in val:
                for req in val["action_requests"]:
                    if req.get("name") == "ask_clarifying_question":
                        is_interactive = True
                        interrogation_question = req.get("args", {}).get("question", "Agent needs clarification.")
                        break
        
        if not is_interactive and messages and hasattr(messages[-1], "tool_calls") and messages[-1].tool_calls:
            for tool_call in messages[-1].tool_calls:
                if tool_call["name"] == "ask_clarifying_question":
                    is_interactive = True
                    interrogation_question = tool_call["args"].get("question", "Agent needs clarification.")
                    break

        # Bundle the result if it was a success and context was saturated
        is_sat = result.get("is_saturated")
        if result and "FAILURE" not in str(result) and not is_interactive and is_sat is not False:
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
                    import re
                    generated_agents = result.get("generated_agents")
                    
                    # If not explicitly provided in state, try to parse markdown output
                    if not generated_agents and "messages" in result:
                        final_content = result["messages"][-1].content
                        yaml_blocks = re.findall(r"```yaml\n(.*?)\n```", final_content, re.DOTALL)
                        if yaml_blocks:
                            generated_agents = {}
                            if len(yaml_blocks) >= 1:
                                generated_agents["orchestrator_agent"] = yaml_blocks[0]
                            if len(yaml_blocks) >= 2:
                                generated_agents["project"] = yaml_blocks[1]

                    if not generated_agents:
                        final_msg = result["messages"][-1].content if "messages" in result else "No messages"
                        logger.warning(f"No 'generated_agents' found in result. Final content was: {final_msg}. Using fallback mock.")
                        generated_agents = {
                            "orchestrator_agent": "name: test_agent\n",
                            "project": "name: test_project\n"
                        }
                        
                    state_payload = {
                        "generated_agents": generated_agents
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
            return {"status": "success", "artifact": zip_path, "details": str(result), "is_saturated": is_sat}
            
        if is_interactive and interrogation_question:
            last_message = interrogation_question
            is_sat = False
        else:
            last_message = result.get("messages", [])[-1].content if result.get("messages") else "Interrogation requested by agent."
            
        return {"status": "failure", "details": last_message, "is_saturated": is_sat}
