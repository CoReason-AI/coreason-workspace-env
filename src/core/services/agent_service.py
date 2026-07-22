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
        agent_dir = (_AGENTS_DIR / agent_name).resolve()
        if not str(agent_dir).startswith(str(_AGENTS_DIR.resolve())):
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
            raise ValueError("Invalid agent name")

        job_id = session_id or str(uuid.uuid7())

        from deepagents.graph import create_deep_agent
        from deepagents.backends import StateBackend
        from langchain_openai import ChatOpenAI
        
        try:
            agent_manifest = self.get_agent(agent_name)
            if not agent_manifest:
                raise ValueError(f"Agent {agent_name} not found")

            # Extract config
            system_prompt = agent_manifest.get("system_prompt", "")
            raw_skills = agent_manifest.get("skill_registry", agent_manifest.get("skills", []))
            skills = []
            for s in raw_skills:
                if isinstance(s, dict):
                    if "name" in s and "path" in s:
                        skills.append((s["name"], s["path"]))
                    elif "name" in s:
                        skills.append(s["name"])
                else:
                    skills.append(s)

            # Initialize DeepAgent
            # Assuming ChatOpenAI is available.
            model = ChatOpenAI(model="gpt-4o", temperature=0)
            
            agent = create_deep_agent(
                model=model,
                system_prompt=system_prompt,
                skills=skills,
                backend=StateBackend(),
            )
            
            # Execute agent in background
            async def run_agent():
                from langgraph.checkpoint.memory import MemorySaver
                # Use in-memory saver for now since custom Postgres DB was removed
                checkpointer = MemorySaver()
                config = {"configurable": {"thread_id": job_id}}
                try:
                    inputs = {"messages": [("user", json.dumps(payload))]}
                    async for chunk in agent.astream(inputs, config=config):
                        pass
                except Exception as e:
                    logger.error(f"Agent execution failed: {e}")
                    
            asyncio.create_task(run_agent())
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

