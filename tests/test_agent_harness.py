import pytest
from src.core.testing.agent_harness import agent_test_harness, TestCaseSpec

@pytest.mark.asyncio
async def test_agent_test_harness_evaluation():
    test_cases = [
        TestCaseSpec(
            name="Basic execution test",
            payload={"query": "test query"},
            expected_status="accepted",
            max_latency_ms=5000.0
        ),
        TestCaseSpec(
            name="Secondary payload test",
            payload={"action": "compile"},
            expected_status="accepted"
        )
    ]
    
    report = await agent_test_harness.run_evaluation(
        agent_name="factory_ceo",
        test_cases=test_cases,
        user_id="test_user",
        tenant_id="test_tenant"
    )
    
    assert report.agent_name == "factory_ceo"
    assert report.total_tests == 2
    assert report.passed_tests == 2
    assert report.pass_rate == 100.0
    assert len(report.results) == 2
    assert report.results[0].passed is True
