import json
import logging
import redis
from typing import Dict, Any

from src.core.config import settings

logger = logging.getLogger(__name__)

class DistributedTaskQueue:
    """
    Decouples the FastAPI core from LangGraph execution via a Redis Task Queue.
    This enables massive map-reduce DAG fanouts without blocking the web servers.
    """
    def __init__(self):
        self.redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.queue_name = "langgraph_execution_queue"
        
    def enqueue_workflow(self, session_id: str, agent_name: str, payload: Dict[str, Any]):
        """
        Pushes a new workflow execution request to the Redis queue.
        KEDA will automatically scale up worker pods based on the length of this queue.
        """
        task = {
            "session_id": session_id,
            "agent_name": agent_name,
            "payload": payload
        }
        self.redis_client.lpush(self.queue_name, json.dumps(task))
        logger.info(f"Enqueued workflow for session {session_id} on {self.queue_name}")

    def dequeue_workflow(self) -> Dict[str, Any]:
        """
        Pulls a workflow execution request from the queue (blocking).
        Used by the stateless KEDA worker pods.
        """
        _, task_json = self.redis_client.brpop(self.queue_name, timeout=0)
        return json.loads(task_json)

# Singleton instance
task_queue = DistributedTaskQueue()
