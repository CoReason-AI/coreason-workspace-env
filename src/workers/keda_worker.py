import logging
import time

from src.core.queue import task_queue
from src.agents.orchestrator import PlatformOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("keda_worker")

def run_worker_loop():
    """
    Stateless KEDA worker loop.
    These Python pods are horizontally autoscaled by Kubernetes based on the Redis queue depth.
    They pull tasks, load the project plugin manifest, and execute the LangGraph.
    """
    logger.info("KEDA Worker started. Waiting for tasks...")
    
    while True:
        try:
            task = task_queue.dequeue_workflow()
            logger.info(f"Processing task for session: {task['session_id']}")
            
            # In a full implementation, this dynamically loads the project plugin manifest.
            # We mock the manifest loading here.
            project_manifest = {
                "agent_name": task["agent_name"],
                "system_prompt": "You are executing in a distributed stateless KEDA pod."
            }
            
            orchestrator = PlatformOrchestrator(project_manifest)
            
            # Extract user input payload
            user_input = task["payload"].get("input", "")
            
            # Execute the deterministic graph using the Postgres Checkpointer
            result = orchestrator.execute_graph(task["session_id"], user_input)
            
            logger.info(f"Task complete for session {task['session_id']}. Result length: {len(result)}")
            
        except Exception as e:
            logger.error(f"Worker encountered an error: {e}")
            time.sleep(1) # Prevent tight crash loops

if __name__ == "__main__":
    run_worker_loop()
