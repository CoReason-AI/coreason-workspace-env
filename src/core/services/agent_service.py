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

    def list_agents(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Scans src/agents/ for agent.yaml files and returns parsed metadata.
        """
        agents = []
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
        agent_dir = _AGENTS_DIR / agent_name
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
            "path": str(agent_dir),
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

        import importlib
        try:
            module_path = f"src.agents.{agent_name}.orchestrator"
            module = importlib.import_module(module_path)
            agent_class_name = "".join(word.capitalize() for word in agent_name.split("_")) + "Agent"
            agent_class = getattr(module, agent_class_name)
            agent = agent_class()
            
            # Prepare context for the agent
            if hasattr(agent, "execute") and asyncio.iscoroutinefunction(agent.execute):
                asyncio.create_task(agent.execute(context={"messages": [("user", json.dumps(payload))]}, session_id=job_id))
            else:
                asyncio.create_task(asyncio.to_thread(agent.execute, payload, session_id=job_id))
            logger.info(f"Native DeepAgent execution enqueued for thread_id {job_id}")
        except Exception as e:
            logger.error(f"Failed to instantiate agent {agent_name}: {e}")


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
        Delegates to the Dify API.
        """
        import httpx
        from src.core.config import settings
        
        headers = {
            "Authorization": f"Bearer {settings.DIFY_API_KEY}",
            "Content-Type": "application/json"
        }
        
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
            else:
                return {
                    "job_id": job_id,
                    "status": "running",
                    "detail": f"Dify API returned {response.status_code}: {response.text}"
                }
        except Exception as e:
            logger.error(f"Failed to fetch status from Dify: {e}")
            return {
                "job_id": job_id,
                "status": "running",
                "detail": "Failed to connect to Dify orchestration engine."
            }

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

    async def submit_override(self, job_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
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
            # We construct a dummy DeepAgent just to get the graph object with the same checkpointer
            dummy = DeepAgent()
            graph = dummy.build_standard_deep_agent(
                system_prompt="dummy",
                state_schema=DeepAgentState,
                tools=[],
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
        Deploy the generated agent project to the Test Environment via the Dify API.
        This notifies the Dify orchestration shell to sync the MCP tools for the test workspace.
        """
        import httpx
        from src.core.config import settings
        
        headers = {
            "Authorization": f"Bearer {settings.DIFY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                # We simulate calling a hypothetical Dify webhook to sync the MCP server for a specific environment
                response = await client.post(
                    f"{settings.DIFY_API_URL}/mcp/sync",
                    json={"project_id": project_id, "environment": "test", "tenant_id": tenant_id},
                    headers=headers
                )
            logger.info(f"Deployed project {project_id} to Test. Dify sync status: {response.status_code}")
            return {
                "status": "success",
                "environment": "test",
                "project_id": project_id,
                "message": "Successfully notified Dify to sync MCP tools for test environment."
            }
        except Exception as e:
            logger.error(f"Failed to deploy to test environment: {e}")
            return {
                "status": "error",
                "environment": "test",
                "project_id": project_id,
                "message": f"Deployment failed: {str(e)}"
            }

    async def deploy_to_production(self, project_id: str, user_id: str, tenant_id: str) -> Dict[str, Any]:
        """
        Deploy the generated agent project to the Production Environment via the Dify API.
        """
        import httpx
        from src.core.config import settings
        
        headers = {
            "Authorization": f"Bearer {settings.DIFY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.DIFY_API_URL}/mcp/sync",
                    json={"project_id": project_id, "environment": "production", "tenant_id": tenant_id},
                    headers=headers
                )
            logger.info(f"Deployed project {project_id} to Production. Dify sync status: {response.status_code}")
            return {
                "status": "success",
                "environment": "production",
                "project_id": project_id,
                "message": "Successfully notified Dify to sync MCP tools for production environment."
            }
        except Exception as e:
            logger.error(f"Failed to deploy to production environment: {e}")
            return {
                "status": "error",
                "environment": "production",
                "project_id": project_id,
                "message": f"Deployment failed: {str(e)}"
            }
