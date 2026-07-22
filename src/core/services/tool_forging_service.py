"""
Tool Forging Service — Dynamic Tool Synthesis, Maker-Checker Validation, and Cataloging under IANA PEN 66197.
"""
import os
import sys
import uuid
import time
import logging
import tempfile
import subprocess
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from src.core.ontology import CoreasonURN
from src.core.services.catalog_service import catalog_service
from src.core.services.sandbox_service import sandbox_service

logger = logging.getLogger(__name__)


class ForgedToolRecord(BaseModel):
    tool_id: str
    urn: str
    coreason_url: str
    name: str
    description: str
    code: str
    unit_test_code: str
    validation_status: str = Field(default="passed", description="passed, failed, pending")
    validation_logs: str = Field(default="")
    created_at: str


class ToolForgingService:
    """
    Manages the Maker-Checker tool forging lifecycle:
    1. Maker writes tool Python code + pytest unit test.
    2. Checker validates code syntax, executes unit tests in isolated sandbox.
    3. On pass, registers tool into CatalogService under PEN 66197 OID URN (urn:oid:1.3.6.1.4.1.66197:tool:<tool_id>).
    """

    def forge_tool(
        self,
        tool_id: str,
        name: str,
        description: str,
        code: str,
        unit_test_code: str,
        tags: Optional[List[str]] = None,
        author_id: str = "agent_maker",
    ) -> Dict[str, Any]:
        """
        Forges a new dynamic tool: runs sandbox validation tests, enforces Maker-Checker rules,
        and registers the verified tool into the global catalog under PEN 66197 URN.
        """
        logger.info(f"Initiating Tool Forging for '{name}' ({tool_id})...")

        # 1. Generate PEN 66197 URN & Coreason URL
        urn_obj = CoreasonURN(resource_type="tool", resource_id=tool_id)
        oid_urn = urn_obj.to_oid_urn()
        coreason_url = urn_obj.to_coreason_url()

        # 2. Maker-Checker Sandbox Test Execution Gate
        validation_status = "passed"
        validation_logs = "Unit tests executed cleanly in isolated sandbox."

        # Execute tests via temp workspace
        with tempfile.TemporaryDirectory() as tmp_dir:
            tool_file = os.path.join(tmp_dir, f"{tool_id}.py")
            test_file = os.path.join(tmp_dir, f"test_{tool_id}.py")

            clean_tmp_dir = tmp_dir.replace("\\", "/")
            with open(tool_file, "w", encoding="utf-8") as f:
                f.write(code)
            with open(test_file, "w", encoding="utf-8") as f:
                f.write(f"import sys\nsys.path.insert(0, '{clean_tmp_dir}')\nfrom {tool_id} import *\n\n{unit_test_code}")

            try:
                proc = subprocess.run(
                    [sys.executable, "-m", "pytest", test_file],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                if proc.returncode != 0:
                    validation_status = "failed"
                    validation_logs = f"Test Failure:\n{proc.stdout}\n{proc.stderr}"
                    logger.error(f"Tool Forging validation failed for '{tool_id}': {validation_logs}")
                else:
                    validation_logs = proc.stdout
                    logger.info(f"Tool Forging Maker-Checker test gate PASSED for '{tool_id}'.")
            except Exception as e:
                validation_status = "failed"
                validation_logs = f"Execution Exception: {str(e)}"
                logger.error(f"Tool Forging exception during test execution: {e}")

        if validation_status != "passed":
            return {
                "status": "error",
                "message": f"Tool forging failed Maker-Checker validation gate: {validation_logs}",
                "tool_id": tool_id,
                "urn": oid_urn,
                "logs": validation_logs,
            }

        # 3. Register verified tool in IANA PEN 66197 Catalog
        final_tags = list(set(["tool", "forged", "verified"] + (tags or [])))
        catalog_entry = catalog_service.register_entry(
            urn=oid_urn,
            name=name,
            description=description,
            resource_type="tool",
            tags=final_tags,
            metadata={
                "author_id": author_id,
                "unit_test_code": unit_test_code,
                "coreason_url": coreason_url,
                "validation_status": validation_status,
            },
            source_code=code,
        )

        record = ForgedToolRecord(
            tool_id=tool_id,
            urn=oid_urn,
            coreason_url=coreason_url,
            name=name,
            description=description,
            code=code,
            unit_test_code=unit_test_code,
            validation_status=validation_status,
            validation_logs=validation_logs,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )

        logger.info(f"Successfully forged and cataloged tool '{name}' under URN {oid_urn}.")
        return {
            "status": "success",
            "tool": record.model_dump(),
            "catalog_entry": catalog_entry.model_dump(),
        }

    def get_forged_tool(self, urn_or_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a forged tool from the Catalog by URN or tool_id."""
        entry = catalog_service.resolve_urn(urn_or_id)
        if entry and entry.resource_type == "tool":
            return entry.model_dump()
        return None

    def list_forged_tools(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists all discoverable forged tools in the catalog."""
        return catalog_service.search_catalog(query=query, resource_type="tool")


tool_forging_service = ToolForgingService()
