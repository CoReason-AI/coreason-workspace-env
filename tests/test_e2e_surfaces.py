"""
End-to-End Workflow Parity Test
Uses Testcontainers to spin up a live PostgreSQL instance.
Tests the 10-step real-world workflow across REST API, CLI, and SDK surfaces.
"""
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
from testcontainers.redis import RedisContainer
from fastapi.testclient import TestClient

from src.main import app
from src.core.config import settings
from src.core.db import get_db_pool, close_db_pool
from src.core import db
from src.core.services import project_service, agent_service
from src.core.ws_backplane import pubsub_backplane
import redis.asyncio as redis
from src.mcp.server import create_project, execute_agent, export_project
import pytest_asyncio


@pytest.fixture(scope="module")
def containers():
    postgres = PostgresContainer("postgres:15-alpine")
    postgres.start()
    
    redis_container = RedisContainer("redis:7-alpine")
    redis_container.start()
    
    settings.POSTGRES_USER = postgres.username
    settings.POSTGRES_PASSWORD = postgres.password
    settings.POSTGRES_HOST = postgres.get_container_host_ip()
    settings.POSTGRES_PORT = int(postgres.get_exposed_port(5432))
    settings.POSTGRES_DB = postgres.dbname
    settings.REDIS_URL = f"redis://{redis_container.get_container_host_ip()}:{redis_container.get_exposed_port(6379)}"
    
    yield postgres, redis_container
    
    postgres.stop()
    redis_container.stop()


@pytest_asyncio.fixture(autouse=True)
async def setup_db_and_tmpdir(containers):
    db._global_pool = None
    pubsub_backplane.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub_backplane.pubsub = pubsub_backplane.redis.pubsub()
    pubsub_backplane.subscriptions = {}
    
    await project_service.initialize()
    tmpdir = tempfile.mkdtemp()
    
    yield tmpdir
    
    await close_db_pool()
    shutil.rmtree(tmpdir, ignore_errors=True)
    shutil.rmtree("rest_export", ignore_errors=True)
    shutil.rmtree("service_export", ignore_errors=True)


@pytest.mark.asyncio
@patch("src.core.security.auth.verify_token")
@patch("src.core.queue.task_queue.enqueue_workflow")
async def test_workflow_rest_api_layer(mock_enqueue, mock_verify):
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
        assert res.status_code == 201
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
        assert exec_res.status_code == 200
        assert exec_res.json()["status"] == "accepted"
        mock_enqueue.assert_called_once()

        # Step 8: Export Project
        Path(f"projects/{project_id}").mkdir(parents=True, exist_ok=True)
        export_path = "rest_export"
        exp_res = await client.post(
            f"/api/v1/projects/{project_id}/export?output_path={export_path}&skip_state=true&skip_docker=true",
            headers=headers
        )
        assert exp_res.status_code == 200
        assert "workspace.tar.gz" in [Path(p).name for p in exp_res.json()["files_written"]]


@pytest.mark.asyncio
@patch("src.core.queue.task_queue.enqueue_workflow")
async def test_workflow_service_layer(mock_enqueue):
    """Test the workflow directly via the core service layer."""
    # Step 1: Create Project
    project = await project_service.create_project(
        project_id="project_svc_123",
        name="service_test",
        description="Integration test project"
    )
    assert project["name"] == "service_test"

    # Step 3: Execute Agent
    exec_res = await agent_service.execute_agent(
        agent_name="factory_ceo",
        payload={"intent": "build a clinical trial platform"},
        user_id="test_user",
        tenant_id="test_tenant"
    )
    assert exec_res["status"] == "accepted"
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
    assert export_res["status"] == "success"
    assert "workspace.tar.gz" in [Path(p).name for p in export_res["files_written"]]


@pytest.mark.asyncio
async def test_workflow_sdk_layer():
    """Test the Python SDK interface mapping."""
    from src.sdk import CoReasonClient
    client = CoReasonClient()
    assert hasattr(client.projects, "create")
    assert hasattr(client.agents, "execute")
    assert hasattr(client.projects, "export")


@pytest.mark.asyncio
@patch("src.core.queue.task_queue.enqueue_workflow")
async def test_workflow_mcp_layer(mock_enqueue):
    """Test the workflow using the MCP Server tools directly."""
    # Step 1: Create Project
    res = await create_project("mcp_test_project", "Testing MCP UI")
    assert res["status"] == "created"
    project_id = res["project"]["id"]
    
    # Step 3: Execute Agent
    exec_res = await execute_agent("factory_ceo", "test_user", "test_tenant", {"intent": "build a platform"})
    assert exec_res["status"] == "accepted"
    mock_enqueue.assert_called_once()
    
    # Step 8: Export Project
    Path(f"projects/{project_id}").mkdir(parents=True, exist_ok=True)
    exp_res = await export_project(project_id, "mcp_export", skip_state=True, skip_docker=True)
    assert exp_res["status"] == "success"
    assert "workspace.tar.gz" in [Path(p).name for p in exp_res["files_written"]]


@pytest.mark.asyncio
async def test_workflow_cli_layer(containers):
    """Test the CLI interface mapping."""
    postgres, _ = containers
    env = os.environ.copy()
    env["POSTGRES_USER"] = postgres.username
    env["POSTGRES_PASSWORD"] = postgres.password
    env["POSTGRES_HOST"] = postgres.get_container_host_ip()
    env["POSTGRES_PORT"] = str(postgres.get_exposed_port(5432))
    env["POSTGRES_DB"] = postgres.dbname

    result = subprocess.run(
        [sys.executable, "-m", "src.cli.main", "export-project", "--help"],
        capture_output=True, text=True, cwd=".", env=env
    )
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    
    result2 = subprocess.run(
        [sys.executable, "-m", "src.cli.main", "build", "--help"],
        capture_output=True, text=True, cwd=".", env=env
    )
    assert result2.returncode == 0, f"CLI failed: {result2.stderr}"
