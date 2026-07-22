import pytest
from typer.testing import CliRunner
import json
from src.cli.main import app

runner = CliRunner()

def test_cli_health():
    result = runner.invoke(app, ["health"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["status"] == "healthy"

def test_cli_agents_list():
    result = runner.invoke(app, ["agents", "list"])
    assert result.exit_code == 0
    assert "agents" in result.stdout

def test_cli_agents_get():
    result = runner.invoke(app, ["agents", "get", "--name", "factory_ceo"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["agent"]["name"] == "factory_ceo"

def test_cli_agents_get_not_found():
    result = runner.invoke(app, ["agents", "get", "--name", "nonexistent_agent"])
    assert result.exit_code == 1
    assert "Not found" in result.stdout

def test_cli_agents_execute():
    result = runner.invoke(app, ["agents", "execute", "--name", "factory_ceo", "--payload", '{"query": "build"}'])
    assert result.exit_code == 0
    json_line = result.stdout.strip().splitlines()[-1]
    data = json.loads(json_line)
    assert data["status"] == "accepted"
    assert "job_id" in data

def test_cli_agents_execute_invalid_json():
    result = runner.invoke(app, ["agents", "execute", "--name", "factory_ceo", "--payload", "invalid_json"])
    assert result.exit_code == 1
    assert "payload must be a valid JSON string" in result.stdout

def test_cli_deploy_test():
    result = runner.invoke(app, ["deploy", "test", "--project-id", "proj_456"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["status"] == "success"
    assert data["deployment"]["environment"] == "test"

def test_cli_deploy_production():
    result = runner.invoke(app, ["deploy", "production", "--project-id", "proj_456"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["status"] == "success"
    assert data["deployment"]["environment"] == "production"

def test_cli_mcp_bundle(tmp_path):
    out_file = str(tmp_path / "bundle.enc")
    result = runner.invoke(app, ["mcp", "bundle", "--source", "src/agents", "--output", out_file])
    assert result.exit_code == 0
    assert "bundled successfully" in result.stdout
