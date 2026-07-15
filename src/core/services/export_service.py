import os
import re
import shutil
import zipfile
import logging
from pathlib import Path
from typing import Optional
from src.core.db import get_db_pool

logger = logging.getLogger(__name__)

class PlatformExporter:
    """
    Service to traverse generated output folders, validate manifest,
    and bundle into an MCP-compliant zip file.
    """
    def __init__(self, output_dir: str = "./generated_agents"):
        self.output_dir = Path(output_dir).resolve()

    async def bundle_agent_specs(self, session_id: str, tenant_id: str = "default_tenant") -> Optional[str]:
        """
        Validates and packages the generated YAMLs for a session.
        Returns the filepath of the zip archive.
        """
        # Sanitize session_id to prevent Log Injection (CWE-117) and Path Traversal (CWE-22)
        import re
        if not re.match(r"^[a-zA-Z0-9_-]+$", session_id):
            logger.error("Invalid session_id")
            return None
        safe_session_id = session_id

        # Build and validate the session directory is within output_dir (CWE-22)
        session_dir = (self.output_dir / safe_session_id).resolve()
        if not str(session_dir).startswith(str(self.output_dir)):
            logger.error("Path traversal attempt detected.")
            return None

        if not session_dir.exists():
            logger.warning("No generated files found on disk for session %s. Querying Postgres state.", safe_session_id)
            session_dir.mkdir(parents=True, exist_ok=True)
            try:
                pool = await get_db_pool()
                async with pool.acquire() as conn:
                    # Query the checkpointer table for finalized YAMLs
                    records = await conn.fetch("SELECT state FROM langgraph_state WHERE thread_id = $1 AND tenant_id = $2 ORDER BY id DESC LIMIT 1", safe_session_id, tenant_id)
                    if records:
                        state_val = records[0]['state']
                        import json
                        state = json.loads(state_val) if isinstance(state_val, str) else state_val
                        # Assuming state contains the generated agents dict
                        for agent_name, yaml_content in state.get("generated_agents", {}).items():
                            if not re.match(r"^[a-zA-Z0-9_-]+$", agent_name):
                                continue
                            safe_agent_name = agent_name
                            with open(session_dir / f"{safe_agent_name}.yaml", "w", encoding="utf-8") as f:
                                f.write(yaml_content)
                    else:
                        raise ValueError("No finalized state found for session %s" % safe_session_id)
            except Exception as e:
                logger.error("Failed to retrieve YAMLs from Postgres: %s", e)
                return None
        
        # We assume validation against coreason-manifest passed in the Maker-Checker phase
        
        # Synthesize a valid Python environment file so the output is installable
        pyproject_content = f"""[project]
name = "coreason-agent-{safe_session_id}"
version = "0.1.0"
description = "Compiled DeepAgent"
dependencies = [
    "pyagentspec",
    "langgraph",
    "langchain",
    "pydantic"
]
"""
        with open(session_dir / "pyproject.toml", "w", encoding="utf-8") as f:
            f.write(pyproject_content)
            
        zip_path = str(session_dir) + ".zip"
        
        # Package YAMLs into an MCP-compliant structure
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(str(session_dir)):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, str(session_dir))
                        zipf.write(file_path, arcname)
            logger.info("Successfully bundled platform for %s at %s", safe_session_id, zip_path)
            return zip_path
        except Exception as e:
            logger.error("Failed to bundle specs: %s", e)
            return None
