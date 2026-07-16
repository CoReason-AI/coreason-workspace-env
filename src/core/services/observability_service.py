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
        
        self.langfuse_host = settings.LANGFUSE_HOST
        self.langfuse_public = settings.LANGFUSE_PUBLIC_KEY
        self.langfuse_secret = settings.LANGFUSE_SECRET_KEY
        
        # Use settings for Vault Address
        self.vault_addr = settings.VAULT_ADDR
        self.vault_token = os.environ.get("VAULT_DEV_ROOT_TOKEN_ID", "root")

    def get_langfuse_callback(self, session_id: str):
        """
        Returns a configured Langchain CallbackHandler for Langfuse.
        """
        from langfuse.callback import CallbackHandler
        if not self.langfuse_public or not self.langfuse_secret:
            logger.warning("Langfuse credentials missing; returning None for callback.")
            return None
            
        return CallbackHandler(
            public_key=self.langfuse_public,
            secret_key=self.langfuse_secret,
            host=self.langfuse_host,
            session_id=session_id
        )

    async def fetch_postgres_state(self, session_id: str) -> Dict[str, Any]:
        """
        Query the postgres_checkpointer DB directly to get the current graph state.
        """
        try:
            conn = await asyncpg.connect(self.pg_dsn)
            query = """
            SELECT thread_id, state 
            FROM langgraph_state 
            WHERE thread_id = $1 
            ORDER BY id DESC LIMIT 1
            """
            row = await conn.fetchrow(query, session_id)
            await conn.close()
            
            if row:
                state_data = json.loads(row["state"]) if isinstance(row["state"], str) else row["state"]
                return {
                    "thread_id": row["thread_id"],
                    "state": state_data
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
        Resumes a paused or failed agent execution via native LangGraph checkpoint state.
        """
        try:
            from src.core.engine.deepagent_runtime import PlatformOrchestrator
            import asyncio
            import json
            orchestrator = PlatformOrchestrator(project_manifest={})
            asyncio.create_task(orchestrator.execute_graph(session_id=session_id, user_input=json.dumps(payload)))
            logger.info(f"LangGraph execution resumed for thread_id {session_id}")
            return {"status": "success", "message": f"Resumed agent {agent_name} for session {session_id}"}
        except Exception as e:
            logger.error(f"Failed to resume agent: {e}")
            return {"error": str(e)}
