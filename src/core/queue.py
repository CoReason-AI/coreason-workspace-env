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
        import os
        self.queue_name = os.getenv("REDIS_QUEUE_NAME", "tasks")
        
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
        from src.core.security.path_validation import sanitize_log_input
        logger.info(f"Enqueued workflow for session {sanitize_log_input(session_id)} on {self.queue_name}")

    def dequeue_workflow(self) -> Dict[str, Any]:
        """
        Pulls a workflow execution request from the queue (non-blocking).
        Used by the stateless KEDA worker pods.
        """
        try:
            result = self.redis_client.lpop(self.queue_name)
            if not result:
                return None
            return json.loads(result)
        except Exception as e:
            logger.error(f"Redis pop error: {e}")
            return None

    def set_job_result(self, job_id: str, result: Dict[str, Any], ttl: int = 86400):
        self.redis_client.setex(f"job_result:{job_id}", ttl, json.dumps(result, default=str))

    def get_job_result(self, job_id: str) -> Dict[str, Any]:
        res = self.redis_client.get(f"job_result:{job_id}")
        return json.loads(res) if res else None

# Singleton instance
task_queue = DistributedTaskQueue()
