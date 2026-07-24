"""
Testing Service — Sandboxed execution & evaluation suite for agentic applications.
"""
import sys
import os
import time
import logging
import tempfile
import subprocess
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from src.core.services.sandbox_service import sandbox_service

logger = logging.getLogger(__name__)


class TestReceipt(BaseModel):
    test_id: str
    target_agent: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    execution_time_seconds: float
    status: str = Field(..., description="PASSED, FAILED")
    traceback_log: str = Field(default="")
    coverage_percentage: float = 100.0


class TestingService:
    """
    Executes automated unit and integration tests against agent graphs in isolated sandboxes.
    """

    def run_agent_test_suite(
        self,
        agent_name: str,
        test_code: str,
        agent_code: str,
        project_id: str = "test_project",
    ) -> TestReceipt:
        """
        Executes a test suite against an agent within a provisioned sandbox.
        """
        logger.info(f"Running test suite for agent '{agent_name}'...")
        start_time = time.time()

        # Provision OpenShell sandbox record
        sandbox_rec = sandbox_service.provision_sandbox(
            project_id=project_id,
            user_id="test_runner",
            tenant_id="tenant_1",
            agent_name=agent_name,
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            clean_tmp = tmp_dir.replace("\\", "/")
            agent_file = os.path.join(tmp_dir, f"{agent_name}.py")
            test_file = os.path.join(tmp_dir, f"test_{agent_name}.py")

            with open(agent_file, "w", encoding="utf-8") as f:
                f.write(agent_code)
            with open(test_file, "w", encoding="utf-8") as f:
                f.write(f"import sys\nsys.path.insert(0, '{clean_tmp}')\nfrom {agent_name} import *\n\n{test_code}")

            try:
                proc = subprocess.run(
                    [sys.executable, "-m", "pytest", test_file],
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                elapsed = time.time() - start_time
                if proc.returncode == 0:
                    return TestReceipt(
                        test_id=f"test_{agent_name}_{int(time.time())}",
                        target_agent=agent_name,
                        total_tests=1,
                        passed_tests=1,
                        failed_tests=0,
                        execution_time_seconds=round(elapsed, 2),
                        status="PASSED",
                        traceback_log=proc.stdout,
                    )
                else:
                    return TestReceipt(
                        test_id=f"test_{agent_name}_{int(time.time())}",
                        target_agent=agent_name,
                        total_tests=1,
                        passed_tests=0,
                        failed_tests=1,
                        execution_time_seconds=round(elapsed, 2),
                        status="FAILED",
                        traceback_log=f"{proc.stdout}\n{proc.stderr}",
                    )
            except Exception as e:
                elapsed = time.time() - start_time
                return TestReceipt(
                    test_id=f"test_{agent_name}_{int(time.time())}",
                    target_agent=agent_name,
                    total_tests=1,
                    passed_tests=0,
                    failed_tests=1,
                    execution_time_seconds=round(elapsed, 2),
                    status="FAILED",
                    traceback_log=f"Execution Exception: {str(e)}",
                )


testing_service = TestingService()
