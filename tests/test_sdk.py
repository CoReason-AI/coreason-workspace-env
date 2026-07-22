import pytest
from src.sdk import CoReasonClient

@pytest.mark.asyncio
async def test_sdk_client():
    client = CoReasonClient()
    
    # Test version
    ver = client.version()
    assert "version" in ver
    
    # Test health check
    health = await client.health()
    assert "status" in health
    
    # Test agent listing
    agents = client.agents.list()
    assert isinstance(agents, list)
    
    # Test get agent
    agent = client.agents.get("factory_ceo")
    assert agent is not None
    assert agent["name"] == "factory_ceo"
    
    # Test execute agent
    res = await client.agents.execute("factory_ceo", payload={"cmd": "test"})
    assert res["status"] == "accepted"
    assert "job_id" in res
