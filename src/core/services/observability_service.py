"""
Observability Service — provides programmatic hooks into the platform's execution layer
for the Agent Improvement System (Antigravity).
"""
import os
import json
import logging
import subprocess
import httpx
from typing import Dict, Any, Optional
import asyncpg

logger = logging.getLogger(__name__)

class ObservabilityService:
    def __init__(self):
        from src.core.config import settings
        
        # Construct DSN from settings for cloud/hybrid compatibility, with optional environment override
        default_dsn = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        self.pg_dsn = os.environ.get("DATABASE_URL", default_dsn)
        
        self.langfuse_host = os.environ.get("LANGFUSE_HOST", "http://localhost:3001")
        self.langfuse_public = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
        self.langfuse_secret = os.environ.get("LANGFUSE_SECRET_KEY", "")
        
        # Use settings for Vault Address
        self.vault_addr = settings.VAULT_ADDR
        self.vault_token = os.environ.get("VAULT_DEV_ROOT_TOKEN_ID", "root")

    async def fetch_postgres_state(self, session_id: str) -> Dict[str, Any]:
        """
        Query the postgres_checkpointer DB directly to get the current graph state.
        """
        try:
            conn = await asyncpg.connect(self.pg_dsn)
            query = """
            SELECT thread_id, checkpoint_id, checkpoint, metadata 
            FROM checkpoints 
            WHERE thread_id = $1 
            ORDER BY checkpoint_id DESC LIMIT 1
            """
            row = await conn.fetchrow(query, session_id)
            await conn.close()
            
            if row:
                return {
                    "thread_id": row["thread_id"],
                    "checkpoint_id": row["checkpoint_id"],
                    "metadata": json.loads(row["metadata"].decode("utf-8")) if isinstance(row["metadata"], bytes) else row["metadata"],
                    "checkpoint_size": len(row["checkpoint"]) if row["checkpoint"] else 0
                }
            return {"error": f"No state found for session {session_id}"}
        except Exception as e:
            logger.error(f"Failed to fetch postgres state: {e}")
            return {"error": str(e)}

    async def fetch_langfuse_traces(self, session_id: str) -> Dict[str, Any]:
        """
        Query the Langfuse local API for traces linked to the session_id.
        """
        if not self.langfuse_public or not self.langfuse_secret:
            return {"error": "Langfuse API keys are not set in environment."}
            
        url = f"{self.langfuse_host}/api/public/traces?tags={session_id}"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url, 
                    auth=(self.langfuse_public, self.langfuse_secret),
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch langfuse traces: {e}")
            return {"error": str(e)}

    async def write_dev_vault_secret(self, secret_path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Writes a secret to the local dev Vault for agent impersonation.
        """
        url = f"{self.vault_addr}/v1/{secret_path}"
        headers = {"X-Vault-Token": self.vault_token}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json={"data": data},
                    timeout=5.0
                )
                response.raise_for_status()
                return {"status": "success", "secret_path": secret_path}
        except Exception as e:
            logger.error(f"Failed to write dev vault secret: {e}")
            return {"error": str(e)}

    async def fetch_docker_logs(self, lines: int = 100) -> str:
        """
        Fetches the last N lines from the platform_worker docker container.
        """
        try:
            cmd = ["docker", "logs", "--tail", str(lines), "coreason-workspace-env-platform_worker-1"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout or result.stderr
        except subprocess.CalledProcessError as e:
            return f"Error fetching logs: {e.stderr}"
        except Exception as e:
            return f"Execution error: {str(e)}"

    async def resume_agent(self, session_id: str, agent_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resumes a paused or failed agent execution by enqueuing a new task to Redis.
        """
        try:
            from src.core.queue import task_queue
            task_queue.enqueue_workflow(
                session_id=session_id,
                agent_name=agent_name,
                payload=payload
            )
            return {"status": "success", "message": f"Resumed agent {agent_name} for session {session_id}"}
        except Exception as e:
            logger.error(f"Failed to resume agent: {e}")
            return {"error": str(e)}
