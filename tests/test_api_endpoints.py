import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_list_agents_api():
    response = client.get("/api/v1/agents/")
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data

def test_get_agent_api():
    response = client.get("/api/v1/agents/factory_ceo")
    assert response.status_code == 200
    data = response.json()
    assert data["agent"]["name"] == "factory_ceo"

def test_get_nonexistent_agent_api():
    response = client.get("/api/v1/agents/nonexistent_agent_999")
    assert response.status_code == 404

def test_execute_agent_api():
    headers = {
        "x-user-id": "dev-user",
        "x-tenant-id": "tenant-1",
        "x-user-roles": "developer"
    }
    payload = {
        "agent_name": "factory_ceo",
        "payload": {"test": True}
    }
    response = client.post("/api/v1/agents/execute", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert "job_id" in data

def test_deploy_to_test_api():
    headers = {
        "x-user-id": "dev-user",
        "x-tenant-id": "tenant-1",
        "x-user-roles": "developer"
    }
    response = client.post("/api/v1/agents/deploy/test/proj_123", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["deployment"]["environment"] == "test"
    assert data["deployment"]["project_id"] == "proj_123"

def test_deploy_to_production_api():
    headers = {
        "x-user-id": "admin-user",
        "x-tenant-id": "tenant-1",
        "x-user-roles": "admin"
    }
    response = client.post("/api/v1/agents/deploy/production/proj_123", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["deployment"]["environment"] == "production"
    assert data["deployment"]["project_id"] == "proj_123"
