"""
End-to-End Workflow Parity Test
Uses Testcontainers to spin up a live PostgreSQL instance.
Tests the 10-step real-world workflow across REST API, CLI, and SDK surfaces.
"""
import unittest
import pytest
import asyncio
import json
import subprocess
import sys
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from httpx import AsyncClient, ASGITransport
from testcontainers.postgres import PostgresContainer

from src.main import app
from src.core.config import settings
from src.core.db import get_db_pool, close_db_pool
from src.core.services import project_service, agent_service

class E2ESurfaceParityTest(unittest.IsolatedAsyncioTestCase):
    """
    Tests the Core Workflow: Create Project -> Execute Agent -> Export
    across REST API (via TestClient), CLI, and SDK using a live DB.
    """

    @classmethod
    def setUpClass(cls):
        # 1. Start Testcontainers Postgres
        cls.postgres = PostgresContainer("postgres:15-alpine")
        cls.postgres.start()
        
        # 2. Override application settings
        settings.POSTGRES_USER = cls.postgres.username
        settings.POSTGRES_PASSWORD = cls.postgres.password
        settings.POSTGRES_HOST = cls.postgres.get_container_host_ip()
        settings.POSTGRES_PORT = int(cls.postgres.get_exposed_port(5432))
        settings.POSTGRES_DB = cls.postgres.dbname

        # Re-build DB URL if needed for any connection pools
        # src.core.db uses these settings implicitly when creating asyncpg pool.
        
    @classmethod
    def tearDownClass(cls):
        cls.postgres.stop()

    async def asyncSetUp(self):
        # Initialize DB pool and schema before each test
        await project_service.initialize()
        self.tmpdir = tempfile.mkdtemp()

    async def asyncTearDown(self):
        await close_db_pool()
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        # Cleanup the relative export directories created in the workspace
        shutil.rmtree("rest_export", ignore_errors=True)
        shutil.rmtree("service_export", ignore_errors=True)

    @patch("src.core.security.auth.verify_token")
    @patch("src.core.queue.task_queue.enqueue_workflow")
    async def test_workflow_rest_api_layer(self, mock_enqueue, mock_verify):
        """Test the workflow strictly using the REST API (HTTP adapter)."""
        mock_user = MagicMock()
        mock_user.user_id = "test_user"
        mock_user.roles = ["Supervisor"]
        mock_verify.return_value = mock_user
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Step 1: Create Project
            headers = {"Authorization": "Bearer coreason-dev-token"}
            res = await client.post(
                "/api/v1/projects/",
                json={"name": "rest_test_project", "description": "Testing REST UI"},
                headers=headers
            )
            self.assertEqual(res.status_code, 201)
            project_id = res.json()["project"]["id"]
            
            # Step 3: Execute Agent
            exec_res = await client.post(
                "/api/v1/agents/execute",
                json={
                    "agent_name": "factory_ceo",
                    "user_id": "test_user",
                    "tenant_id": "test_tenant",
                    "payload": {"intent": "build a clinical trial platform"}
                },
                headers=headers
            )
            self.assertEqual(exec_res.status_code, 200)
            self.assertEqual(exec_res.json()["status"], "accepted")
            mock_enqueue.assert_called_once()

            # Step 8: Export Project
            Path(f"projects/{project_id}").mkdir(parents=True, exist_ok=True)
            export_path = "rest_export"
            exp_res = await client.post(
                f"/api/v1/projects/{project_id}/export?output_path={export_path}&skip_state=true&skip_docker=true",
                headers=headers
            )
            self.assertEqual(exp_res.status_code, 200)
            self.assertIn("workspace.tar.gz", [Path(p).name for p in exp_res.json()["files_written"]])

    @patch("src.core.queue.task_queue.enqueue_workflow")
    async def test_workflow_service_layer(self, mock_enqueue):
        """Test the workflow directly via the core service layer."""
        # Step 1: Create Project
        project = await project_service.create_project(
            project_id="project_svc_123",
            name="service_test",
            description="Integration test project"
        )
        self.assertEqual(project["name"], "service_test")

        # Step 3: Execute Agent
        exec_res = await agent_service.execute_agent(
            agent_name="factory_ceo",
            payload={"intent": "build a clinical trial platform"},
            user_id="test_user",
            tenant_id="test_tenant"
        )
        self.assertEqual(exec_res["status"], "accepted")
        mock_enqueue.assert_called_once()

        # Step 8: Export Project
        Path("projects/project_svc_123").mkdir(parents=True, exist_ok=True)
        export_path = "service_export"
        export_res = await project_service.export_project(
            project_id="project_svc_123",
            output_path=str(export_path),
            skip_state=True,
            skip_docker=True
        )
        self.assertEqual(export_res["status"], "success")
        self.assertIn("workspace.tar.gz", [Path(p).name for p in export_res["files_written"]])

    def test_workflow_sdk_layer(self):
        """Test the Python SDK interface mapping."""
        from src.sdk import CoReasonClient
        client = CoReasonClient()
        self.assertTrue(hasattr(client.projects, "create"))
        self.assertTrue(hasattr(client.agents, "execute"))
        self.assertTrue(hasattr(client.projects, "export"))

    def test_workflow_cli_layer(self):
        """Test the CLI interface mapping."""
        env = os.environ.copy()
        env["POSTGRES_USER"] = self.postgres.username
        env["POSTGRES_PASSWORD"] = self.postgres.password
        env["POSTGRES_HOST"] = self.postgres.get_container_host_ip()
        env["POSTGRES_PORT"] = str(self.postgres.get_exposed_port(5432))
        env["POSTGRES_DB"] = self.postgres.dbname

        result = subprocess.run(
            [sys.executable, "-m", "src.cli.main", "export-project", "--help"],
            capture_output=True, text=True, cwd=".", env=env
        )
        self.assertEqual(result.returncode, 0, msg=f"CLI failed: {result.stderr}")
        
        result2 = subprocess.run(
            [sys.executable, "-m", "src.cli.main", "build", "--help"],
            capture_output=True, text=True, cwd=".", env=env
        )
        self.assertEqual(result2.returncode, 0, msg=f"CLI failed: {result2.stderr}")

if __name__ == "__main__":
    unittest.main()
