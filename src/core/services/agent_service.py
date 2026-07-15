"""
Agent Service — agent discovery, introspection, and execution.
"""
import json
import logging
import uuid
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

import yaml

logger = logging.getLogger(__name__)

# Resolve agents directory relative to this module
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
                    # Support both skill_registry (new) and skills (legacy)
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
        from src.core.security.path_validation import validate_alphanumeric
        try:
            validate_alphanumeric(agent_name)
        except ValueError:
            return None

        base_dir = _AGENTS_DIR.resolve()
        agent_dir = (base_dir / agent_name).resolve()
        try:
            agent_dir.relative_to(base_dir)
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
        # Support both skill_registry (new) and skills (legacy)
        if "skill_registry" in data:
            result["skill_registry"] = data["skill_registry"]
        else:
            result["skills"] = data.get("skills", [])

        # Include orchestrator source if present
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
        Enqueue an agent execution via the Redis task queue.
        Traces the execution via the Langfuse/WORM bridge.
        Returns a job_id for polling.
        """
        from src.core.security.path_validation import validate_alphanumeric, sanitize_log_input
        validate_alphanumeric(agent_name)

        from src.core.queue import task_queue

        job_id = session_id or str(uuid.uuid7())

        task_queue.enqueue_workflow(
            session_id=job_id,
            agent_name=agent_name,
            payload={
                "user_id": user_id,
                "tenant_id": tenant_id,
                **payload,
            },
        )

        # Trace the execution enqueue via the Langfuse/WORM bridge
        try:
            from src.core.tracing.langfuse_bridge import tracing_bridge
            safe_agent_name = sanitize_log_input(agent_name)
            safe_user_id = sanitize_log_input(user_id)
            tracing_bridge.trace_agent_thought(
                agent_id=safe_agent_name,
                run_id=job_id,
                thought=f"[EXECUTION_ENQUEUED] Agent '{safe_agent_name}' execution enqueued by user '{safe_user_id}'",
                metadata={
                    "event": "execution_enqueued",
                    "user_id": safe_user_id,
                    "tenant_id": sanitize_log_input(tenant_id),
                    "artifact_type": payload.get("artifact_type"),
                },
            )
        except Exception as e:
            logger.warning(f"Tracing failed (non-fatal): {e}")

        return {
            "status": "accepted",
            "job_id": job_id,
            "agent_name": agent_name,
            "message": f"Agent '{agent_name}' execution enqueued.",
            "poll_url": f"/api/v2/jobs/{job_id}",
        }

    def get_execution_status(self, job_id: str) -> Dict[str, Any]:
        """
        Check the status of a previously enqueued job.
        For now, returns a placeholder — real implementation would
        query Postgres LangGraph checkpointer for thread state.
        """
        # TODO: Query Postgres checkpointer for actual thread state
        return {
            "job_id": job_id,
            "status": "running",
            "detail": "LangGraph execution in progress. Query the checkpointer for live state.",
        }

    def rewind_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """
        Rewind a session's LangGraph execution state to a specific checkpoint.
        For now, returns a dummy success response.
        """
        # Validate checkpoint_id as a UUID to prevent log/path injection
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
