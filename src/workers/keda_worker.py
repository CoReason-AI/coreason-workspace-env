import logging
import time
import os
import importlib
import asyncio

from src.core.queue import task_queue

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("keda_worker")

async def run_worker_loop():
    """
    Stateless KEDA worker loop.
    These Python pods are horizontally autoscaled by Kubernetes based on the Redis queue depth.
    They pull tasks, load the project plugin manifest, and execute the LangGraph.
    """
    logger.info("KEDA Worker started. Waiting for tasks...")
    
    while True:
        try:
            task = task_queue.dequeue_workflow()
            if not task:
                await asyncio.sleep(1)
                continue
                
            session_id = task.get("session_id")
            logger.info(f"Processing task for session: {session_id}")
            
            agent_name = task.get("agent_name", "factory_ceo")
            
            # Dynamically load the agent
            module_path = os.environ.get("AGENT_ENTRYPOINT_MODULE", f"src.agents.{agent_name}.orchestrator")
            class_name = os.environ.get("AGENT_ENTRYPOINT_CLASS", "FactoryCeoAgent")
            
            try:
                module = importlib.import_module(module_path)
                AgentClass = getattr(module, class_name)
                agent = AgentClass()
            except (ImportError, AttributeError) as e:
                logger.error(f"Failed to dynamically load agent {module_path}.{class_name}: {e}")
                continue
            
            # Extract user input payload
            user_input = task["payload"].get("input", "")
            
            from langchain_core.messages import HumanMessage
            context = {
                "messages": [HumanMessage(content=user_input)],
                "raw_transcript": user_input
            }
            
            # Execute the deterministic graph using the Postgres Checkpointer
            result = await agent.execute(context, session_id)
            
            logger.info(f"Task complete for session {session_id}. Result length: {len(str(result))}")
            
        except Exception as e:
            logger.error(f"Worker encountered an error: {e}")
            await asyncio.sleep(1) # Prevent tight crash loops

if __name__ == "__main__":
    asyncio.run(run_worker_loop())
