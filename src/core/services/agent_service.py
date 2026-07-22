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
        Traces the execution via the LangSmith/WORM bridge.
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
