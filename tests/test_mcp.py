import pytest
import asyncio
from src.mcp.server import (
    mcp,
    health_check,
    get_version,
    list_agents,
    get_agent,
    execute_agent,
    deploy_to_test,
    deploy_to_production,
    BearerAuthMiddleware
)
from starlette.requests import Request
from starlette.responses import JSONResponse

@pytest.mark.asyncio
async def test_mcp_health_check():
    result = await health_check()
    assert "status" in result

@pytest.mark.asyncio
async def test_mcp_get_version():
    result = await get_version()
    assert "version" in result

@pytest.mark.asyncio
async def test_mcp_list_agents():
    result = await list_agents()
    assert "agents" in result

@pytest.mark.asyncio
async def test_mcp_get_agent_found():
    result = await get_agent("factory_ceo")
    assert "agent" in result
    assert result["agent"]["name"] == "factory_ceo"

@pytest.mark.asyncio
async def test_mcp_get_agent_not_found():
    result = await get_agent("nonexistent_agent_999")
    assert "error" in result
    assert result["error"] == "Not found"

@pytest.mark.asyncio
async def test_mcp_execute_agent():
    result = await execute_agent(
        agent_name="factory_ceo",
        user_id="mcp_user",
        tenant_id="mcp_tenant",
        roles=["developer"],
        payload={"task": "build"}
    )
    assert result["status"] == "accepted"
    assert "job_id" in result

@pytest.mark.asyncio
async def test_mcp_deploy_to_test():
    result = await deploy_to_test(
        project_id="proj_mcp_1",
        user_id="mcp_user",
        tenant_id="mcp_tenant",
        roles=["developer"]
    )
    assert result["status"] == "success"
    assert result["environment"] == "test"

@pytest.mark.asyncio
async def test_mcp_deploy_to_production():
    result = await deploy_to_production(
        project_id="proj_mcp_1",
        user_id="admin_user",
        tenant_id="mcp_tenant",
        roles=["admin"]
    )
    assert result["status"] == "success"
    assert result["environment"] == "production"

@pytest.mark.asyncio
async def test_bearer_auth_middleware_missing_key(monkeypatch):
    monkeypatch.delenv("MCP_API_KEY", raising=False)
    middleware = BearerAuthMiddleware(app=None)
    
    scope = {"type": "http", "headers": []}
    request = Request(scope)
    response = await middleware.dispatch(request, None)
    assert response.status_code == 500

@pytest.mark.asyncio
async def test_bearer_auth_middleware_unauthorized(monkeypatch):
    monkeypatch.setenv("MCP_API_KEY", "secret_key_123")
    middleware = BearerAuthMiddleware(app=None)
    
    scope = {"type": "http", "headers": []}
    request = Request(scope)
    response = await middleware.dispatch(request, None)
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_bearer_auth_middleware_success(monkeypatch):
    monkeypatch.setenv("MCP_API_KEY", "secret_key_123")
    middleware = BearerAuthMiddleware(app=None)
    
    headers = [(b"authorization", b"Bearer secret_key_123")]
    scope = {"type": "http", "headers": headers}
    request = Request(scope)
    
    async def dummy_call_next(req):
        return JSONResponse({"status": "ok"})
        
    response = await middleware.dispatch(request, dummy_call_next)
    assert response.status_code == 200
