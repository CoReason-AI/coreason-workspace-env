import pytest
import asyncio
from src.mcp.server import mcp, health_check, list_agents, get_agent

@pytest.mark.asyncio
async def test_mcp_health_check():
    result = await health_check()
    assert "status" in result

@pytest.mark.asyncio
async def test_mcp_list_agents():
    result = await list_agents()
    assert "agents" in result

@pytest.mark.asyncio
async def test_mcp_get_agent_not_found():
    result = await get_agent("nonexistent_agent_999")
    assert "error" in result
    assert result["error"] == "Not found"
