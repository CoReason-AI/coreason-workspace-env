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
    
    # Test skills namespace
    skills = client.skills.list()
    assert isinstance(skills, list)
    assert len(skills) > 0
    
    fetched_skill = client.skills.get(skills[0]["name"])
    assert fetched_skill is not None
    
    # Test sandboxes namespace
    sbx = client.sandboxes.provision(project_id="proj_sdk_test")
    assert sbx["sandbox_id"] is not None
    
    sbx_info = client.sandboxes.get(sbx["sandbox_id"])
    assert sbx_info is not None
    
    exec_sbx = client.sandboxes.execute(sbx["sandbox_id"], payload={"action": "test"})
    assert exec_sbx["status"] == "success"
    
    term_sbx = client.sandboxes.terminate(sbx["sandbox_id"])
    assert term_sbx["status"] == "success"
    
    # Test catalog namespace
    cat_results = client.catalog.search(query="causal")
    assert isinstance(cat_results, list)
    
    resolved_cat = client.catalog.resolve("urn:oid:1.3.6.1.4.1.66197:project:epistemic_analyst_v1")
    assert resolved_cat is not None
    
    imported_cat = client.catalog.import_module("urn:oid:1.3.6.1.4.1.66197:project:epistemic_analyst_v1", "proj_sdk_target")
    assert imported_cat["status"] == "success"
    
    # Test traces namespace
    trace = client.traces.get(job_id)
    assert trace is not None
    assert trace["job_id"] == job_id
    
    # Test evaluate
    report = await client.agents.evaluate("factory_ceo", test_cases=[
        {"name": "SDK eval test", "payload": {"cmd": "eval"}, "expected_status": "accepted"}
    ])
    assert report["passed_tests"] == 1
