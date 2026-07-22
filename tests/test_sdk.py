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
    
    job_id = res["job_id"]
    
    # Test traces namespace
    trace = client.traces.get(job_id)
    assert trace is not None
    assert trace["job_id"] == job_id
    
    # Test evaluate
    report = await client.agents.evaluate("factory_ceo", test_cases=[
        {"name": "SDK eval test", "payload": {"cmd": "eval"}, "expected_status": "accepted"}
    ])
    assert report["passed_tests"] == 1
