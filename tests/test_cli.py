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

def test_cli_agents_get_not_found():
    result = runner.invoke(app, ["agents", "get", "--name", "nonexistent_agent"])
    assert result.exit_code == 1
    assert "Not found" in result.stdout
