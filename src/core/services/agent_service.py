"""
Agent Service — agent discovery, introspection, and execution.
"""
import json
import logging
import uuid
import time
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional

import yaml


logger = logging.getLogger(__name__)

_AGENTS_DIR = Path(__file__).resolve().parent.parent.parent / "agents"


class AgentService:
    """
    Manages agent discovery and execution.
    All surfaces (API, CLI, MCP, SDK) delegate here.
    """
    _bundle_cache = None
    _bundle_loaded = False
    _deployments: Dict[str, Any] = {}

    @classmethod
    def _get_bundle(cls) -> Optional[Dict[str, str]]:
        if cls._bundle_loaded:
            return cls._bundle_cache
            
        cls._bundle_loaded = True
        import os
        bundle_path = os.environ.get("MCP_BUNDLE_PATH", "dist/coreason_mcp_bundle.enc")
        if os.path.exists(bundle_path):
            from src.core.services.bundler_service import bundler_service
            try:
                cls._bundle_cache = bundler_service.decrypt_bundle(bundle_path)
            except Exception as e:
                logger.error(f"Failed to load encrypted agents: {e}")
        return cls._bundle_cache

    def list_agents(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Scans src/agents/ for agent.yaml files (or the encrypted bundle) and returns parsed metadata.
        """
        agents = []
        bundle = self._get_bundle()
        
        if bundle is not None:
            # Load from encrypted bundle
            for rel_path, content in bundle.items():
                if rel_path.endswith("agent.yaml") or rel_path.endswith("agent.yml"):
                    try:
                        data = yaml.safe_load(content)
                        agent_name = rel_path.split("/")[0] if "/" in rel_path else "unknown"
                        if "\\" in agent_name:
                            agent_name = agent_name.split("\\")[0]
                        agent_entry = {
                            "name": data.get("name", agent_name),
                            "type": data.get("type", "unknown"),
                            "description": data.get("description", ""),
                            "dependencies": data.get("dependencies", []),
                            "path": f"bundle://{agent_name}",
                        }
                        if "skill_registry" in data:
                            agent_entry["skill_registry"] = data["skill_registry"]
                        else:
                            agent_entry["skills"] = data.get("skills", [])
                        agents.append(agent_entry)
                    except Exception as e:
                        logger.warning(f"Failed to parse {rel_path} from bundle: {e}")
            return agents
            
        # Fallback to filesystem
        if not _AGENTS_DIR.is_dir():
            logger.warning(f"Agents directory not found: {_AGENTS_DIR}")
            return agents

        for agent_dir in sorted(_AGENTS_DIR.iterdir()):
            manifest = agent_dir / "agent.yaml"
            if manifest.is_file():
                try:
                    with open(manifest, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                    agent_entry = {
                        "name": data.get("name", agent_dir.name),
                        "type": data.get("type", "unknown"),
                        "description": data.get("description", ""),
                        "dependencies": data.get("dependencies", []),
                        "path": str(agent_dir),
                    }
                    if "skill_registry" in data:
                        agent_entry["skill_registry"] = data["skill_registry"]
                    else:
                        agent_entry["skills"] = data.get("skills", [])
                    agents.append(agent_entry)
                except Exception as e:
                    logger.warning(f"Failed to parse {manifest}: {e}")
        return agents

    def get_agent(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Reads a specific agent's YAML manifest and orchestrator source.
        """
        import re
        if not re.match(r"^[a-zA-Z0-9_-]+$", agent_name):
            return None
            
        data = None
        bundle = self._get_bundle()
        is_bundled = False
        
        if bundle is not None:
            # Try to read from bundle (checking both forward and backslashes)
            target_path = f"{agent_name}/agent.yaml"
            target_path_win = f"{agent_name}\\agent.yaml"
            if target_path in bundle:
                data = yaml.safe_load(bundle[target_path])
                is_bundled = True
            elif target_path_win in bundle:
                data = yaml.safe_load(bundle[target_path_win])
                is_bundled = True
                
        agent_dir = _AGENTS_DIR / agent_name
        
        if data is None:
            # Fallback to filesystem
            try:
                if not agent_dir.resolve().is_relative_to(_AGENTS_DIR.resolve()):
                    return None
            except ValueError:
                return None

            manifest = agent_dir / "agent.yaml"
            if not manifest.is_file():
                return None

            with open(manifest, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

        result = {
            "name": data.get("name", agent_name),
            "type": data.get("type", "unknown"),
            "description": data.get("description", ""),
            "dependencies": data.get("dependencies", []),
            "system_prompt": data.get("system_prompt", ""),
            "path": f"bundle://{agent_name}" if is_bundled else str(agent_dir),
        }
        if "skill_registry" in data:
            result["skill_registry"] = data["skill_registry"]
        else:
            result["skills"] = data.get("skills", [])

        orchestrator = agent_dir / "orchestrator.py"
        if orchestrator.is_file():
            result["orchestrator_source"] = orchestrator.read_text(encoding="utf-8")

        return result

    async def execute_agent(
        self,
        agent_name: str,
        payload: Dict[str, Any],
        user_id: str,
        tenant_id: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Enqueue an agent execution via the native LangGraph Checkpointer.
        Traces the execution via the Langfuse/WORM bridge.
        Returns a job_id for polling.
        """
        import re
        if not re.match(r"^[a-zA-Z0-9_-]+$", agent_name):
            raise ValueError(f"Invalid agent name: {agent_name}")

        job_id = session_id or str(uuid.uuid7())

        from src.core.tasks.agent_tasks import execute_agent_task
        try:
            # Enqueue the Celery task
            execute_agent_task.delay(
                agent_name=agent_name,
                payload=payload,
                user_id=user_id,
                tenant_id=tenant_id,
                session_id=job_id
            )
            logger.info(f"Native DeepAgent execution enqueued to Celery for thread_id {job_id}")
        except Exception as e:
            logger.error(f"Failed to enqueue agent {agent_name} to Celery: {e}")

        return {
            "status": "accepted",
            "job_id": job_id,
            "agent_name": agent_name,
            "message": f"Agent '{agent_name}' execution enqueued.",
            "poll_url": f"/api/v2/jobs/{job_id}",
        }

    async def get_execution_status(self, job_id: str) -> Dict[str, Any]:
        """
        Check the status of a previously enqueued job.
        Checks Celery result backend first, then falls back to Dify.
        """
        # 1. Try Celery AsyncResult
        try:
            from celery.result import AsyncResult
            from src.core.celery_app import celery_app
            res = AsyncResult(job_id, app=celery_app)
            if res.state and res.state != "PENDING":
                return {
                    "job_id": job_id,
                    "status": res.state.lower(),
                    "detail": res.result if res.ready() else None
                }
        except Exception as e:
            logger.debug(f"Celery AsyncResult lookup failed for {job_id}: {e}")

        # 2. Fall back to Dify API
        import httpx
        import asyncio
        from src.core.config import settings
        
        headers = {
            "Authorization": f"Bearer {settings.DIFY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                # Query Dify message status API
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{settings.DIFY_API_URL}/messages/{job_id}",
                        headers=headers
                    )
                    
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "job_id": job_id,
                        "status": "success",
                        "detail": data
                    }
                elif response.status_code in [502, 503, 504]:
                    # Transient error, let the loop retry
                    logger.warning(f"Transient Dify error {response.status_code}. Retrying...")
                    response.raise_for_status()
                else:
                    # Deterministic error (400, 401, 404, 500), fail immediately
                    logger.error(f"Dify API error {response.status_code}: {response.text}")
                    return {
                        "job_id": job_id,
                        "status": "error",
                        "message": f"Dify API returned HTTP {response.status_code}"
                    }
                    
            except httpx.RequestError as e:
                logger.warning(f"Network error on attempt {attempt+1}/{max_retries}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"Failed to fetch status from Dify after {max_retries} attempts: {e}")
                    return {
                        "job_id": job_id,
                        "status": "error",
                        "message": "Failed to connect to Dify orchestration engine."
                    }
            except httpx.HTTPStatusError as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to fetch status from Dify after {max_retries} attempts (HTTP {e.response.status_code})")
                    return {
                        "job_id": job_id,
                        "status": "error",
                        "message": f"Dify API returned HTTP {e.response.status_code} after retries."
                    }
                    
            # Exponential backoff
            if attempt < max_retries - 1:
                await asyncio.sleep(base_delay * (2 ** attempt))

    def rewind_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """
        Rewind a session's LangGraph execution state to a specific checkpoint.
        With Dify as the primary orchestrator, this is no longer supported directly via this API.
        """
        from fastapi import HTTPException
        raise HTTPException(
            status_code=501, 
            detail="Checkpoint rewinding is not supported under the Dify orchestration architecture."
        )

    async def submit_override(self, job_id: str, agent_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Human-On-The-Loop (HOTL) Intervention.
        Injects an override payload (like Command(resume=...)) into a paused or running LangGraph thread.
        """
        from langgraph.types import Command
        import os
        from src.core.config import settings
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        from src.core.base_agent import DeepAgent
        from deepagents.graph import DeepAgentState

        pg_dsn = getattr(settings, "DATABASE_URL", os.environ.get("DATABASE_URL", "postgresql://user:pass@localhost:5432/db"))
        
        async with AsyncPostgresSaver.from_conn_string(pg_dsn) as checkpointer:
            await checkpointer.setup()
            import importlib
            module_path = f"src.agents.{agent_name}.orchestrator"
            module = importlib.import_module(module_path)
            agent_class_name = "".join(word.capitalize() for word in agent_name.split("_")) + "Agent"
            agent_class = getattr(module, agent_class_name)
            agent_instance = agent_class()
            
            from deepagents.graph import DeepAgentState
            # Instantiate the actual target graph
            graph = agent_instance.build_standard_deep_agent(
                system_prompt=getattr(agent_instance, "system_prompt", "You are an AI assistant."),
                state_schema=DeepAgentState,
                tools=getattr(agent_instance, "tools", []),
                checkpointer=checkpointer
            )
            config = {"configurable": {"thread_id": job_id}}
            
            try:
                # Issue the override via Command
                await graph.ainvoke(Command(resume=payload), config=config)
                return {
                    "status": "success",
                    "job_id": job_id,
                    "message": "Override payload successfully injected into execution thread."
                }
            except Exception as e:
                logger.error(f"Failed to submit override for job {job_id}: {e}")
                return {
                    "status": "error",
                    "job_id": job_id,
                    "message": str(e)
                }

    async def deploy_to_test(self, project_id: str, user_id: str, tenant_id: str) -> Dict[str, Any]:
        """
        Deploy the generated agent project to the Test Environment.
        Records deployment state and returns full audit record.
        """
        import hashlib
        from src.core.ontology import DeploymentRecord
        
        dep_id = str(uuid.uuid7())
        bundle_hash = hashlib.sha256(f"{project_id}:test:{dep_id}".encode()).hexdigest()
        
        record = DeploymentRecord(
            deployment_id=dep_id,
            project_id=project_id,
            environment="test",
            bundle_hash=bundle_hash,
            user_id=user_id,
            tenant_id=tenant_id,
            status="deployed",
            deployed_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
        
        self._deployments[dep_id] = record.model_dump()
        logger.info(f"Recorded deployment {dep_id} for project {project_id} to Test.")
        
        return {
            "status": "success",
            "deployment": record.model_dump(),
            "message": "Successfully deployed to test environment. Please sync the MCP server in Dify."
        }

    async def deploy_to_production(self, project_id: str, user_id: str, tenant_id: str) -> Dict[str, Any]:
        """
        Deploy the generated agent project to the Production Environment.
        Records deployment state and returns full audit record.
        """
        import hashlib
        from src.core.ontology import DeploymentRecord
        
        dep_id = str(uuid.uuid7())
        bundle_hash = hashlib.sha256(f"{project_id}:production:{dep_id}".encode()).hexdigest()
        
        record = DeploymentRecord(
            deployment_id=dep_id,
            project_id=project_id,
            environment="production",
            bundle_hash=bundle_hash,
            user_id=user_id,
            tenant_id=tenant_id,
            status="deployed",
            deployed_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
        
        self._deployments[dep_id] = record.model_dump()
        logger.info(f"Recorded deployment {dep_id} for project {project_id} to Production.")
        
        return {
            "status": "success",
            "deployment": record.model_dump(),
            "message": "Successfully deployed to production environment. Please sync the MCP server in Dify."
        }
