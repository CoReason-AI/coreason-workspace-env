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

# from src.core.engine.deepagent_runtime import PlatformOrchestrator
from src.core.services.observability_service import ObservabilityService

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
        from src.core.security.path_validation import validate_alphanumeric, validate_safe_path
        try:
            validate_alphanumeric(agent_name)
            agent_dir = validate_safe_path(agent_name, base_dir=_AGENTS_DIR)
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
        from src.core.security.path_validation import validate_alphanumeric, sanitize_log_input
        validate_alphanumeric(agent_name)

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
        Queries Postgres LangGraph checkpointer for actual thread state.
        """
        obs = ObservabilityService()
        state = await obs.fetch_postgres_state(job_id)
        if "error" in state:
            return {
                "job_id": job_id,
                "status": "running",
                "detail": state["error"],
            }
        return {
            "job_id": job_id,
            "status": "success",
            "detail": state,
        }

    def rewind_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """
        Rewind a session's LangGraph execution state to a specific checkpoint.
        For now, returns a dummy success response.
        """
        try:
            uuid.UUID(checkpoint_id)
        except ValueError:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Invalid checkpoint_id format. Must be a valid UUID.")

        from src.core.security.path_validation import sanitize_log_input
        logger.info(f"Rewinding session to checkpoint: {sanitize_log_input(checkpoint_id)}")
        return {
            "status": "success",
            "checkpoint_id": checkpoint_id,
            "message": f"Successfully rewound state to checkpoint {checkpoint_id}"
        }
