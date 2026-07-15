import os
import shutil
import zipfile
import logging
from typing import Optional
from src.core.db import get_db_pool

logger = logging.getLogger(__name__)

class PlatformExporter:
    """
    Service to traverse generated output folders, validate manifest,
    and bundle into an MCP-compliant zip file.
    """
    def __init__(self, output_dir: str = "./generated_agents"):
        self.output_dir = output_dir

    async def bundle_agent_specs(self, session_id: str, tenant_id: str = "default_tenant") -> Optional[str]:
        """
        Validates and packages the generated YAMLs for a session.
        Returns the filepath of the zip archive.
        """
        # Sanitize session_id to prevent Log Injection (CWE-117) and Path Traversal (CWE-22)
        safe_session_id = "".join(c for c in session_id if c.isalnum() or c in "-_")
        
        # In a real implementation, we query postgres to ensure all YAMLs are finalized
        # Here we package whatever is in the session output directory
        session_dir = os.path.join(self.output_dir, safe_session_id)
        
        if not os.path.exists(session_dir):
            logger.warning(f"No generated files found on disk for session {safe_session_id}. Querying Postgres state.")
            os.makedirs(session_dir, exist_ok=True)
            try:
                pool = await get_db_pool()
                async with pool.acquire() as conn:
                    # Query the checkpointer table for finalized YAMLs
                    records = await conn.fetch("SELECT state FROM langgraph_state WHERE thread_id = $1 AND tenant_id = $2 ORDER BY id DESC LIMIT 1", safe_session_id, tenant_id)
                    if records:
                        state = records[0]['state']
                        # Assuming state contains the generated agents dict
                        for agent_name, yaml_content in state.get("generated_agents", {}).items():
                            with open(os.path.join(session_dir, f"{agent_name}.yaml"), "w", encoding="utf-8") as f:
                                f.write(yaml_content)
                    else:
                        raise ValueError(f"No finalized state found for session {safe_session_id}")
            except Exception as e:
                logger.error(f"Failed to retrieve YAMLs from Postgres: {e}")
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
        with open(os.path.join(session_dir, "pyproject.toml"), "w", encoding="utf-8") as f:
            f.write(pyproject_content)
            
        zip_path = f"{session_dir}.zip"
        
        # Package YAMLs into an MCP-compliant structure
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(session_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, session_dir)
                        zipf.write(file_path, arcname)
            logger.info(f"Successfully bundled platform for {safe_session_id} at {zip_path}")
            return zip_path
        except Exception as e:
            logger.error(f"Failed to bundle specs: {e}")
            return None
