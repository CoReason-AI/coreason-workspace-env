import time
import uuid
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from src.core.services import agent_service
from src.core.services.trace_service import trace_service

logger = logging.getLogger(__name__)


class TestCaseSpec(BaseModel):
    __test__ = False
    test_id: str = Field(default_factory=lambda: str(uuid.uuid7()))
    name: str
    payload: Dict[str, Any]
    expected_status: str = Field(default="accepted")
    max_latency_ms: Optional[float] = None
    expected_output_contains: Optional[List[str]] = None


class TestResult(BaseModel):
    test_id: str
    name: str
    passed: bool
    status_code: str
    latency_ms: float
    error_message: Optional[str] = None
    trace: Optional[Dict[str, Any]] = None


class EvaluationReport(BaseModel):
    report_id: str = Field(default_factory=lambda: str(uuid.uuid7()))
    agent_name: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    pass_rate: float
    results: List[TestResult]
    evaluated_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))


class AgentTestHarness:
    """
    Evaluation Engine for factory agents.
    Allows factory agents (e.g. agent_tester, factory_ceo) to execute unit and E2E evaluation suites
    against target agentic applications and inspect trace results.
    """

    async def run_evaluation(
        self,
        agent_name: str,
        test_cases: List[TestCaseSpec],
        user_id: str = "harness-user",
        tenant_id: str = "harness-tenant",
    ) -> EvaluationReport:
        results = []
        passed_count = 0

        for tc in test_cases:
            start_t = time.time()
            error_msg = None
            passed = False
            status = "unknown"

            try:
                res = await agent_service.execute_agent(
                    agent_name=agent_name,
                    payload=tc.payload,
                    user_id=user_id,
                    tenant_id=tenant_id,
                )
                status = res.get("status", "unknown")
                job_id = res.get("job_id", "")
                
                # Check status pass condition
                if status == tc.expected_status:
                    passed = True
                else:
                    error_msg = f"Expected status {tc.expected_status}, got {status}"

                # Fetch execution trace if available
                trace_data = trace_service.get_trace(job_id) if job_id else None

            except Exception as e:
                error_msg = str(e)
                status = "error"
                trace_data = None

            end_t = time.time()
            latency_ms = round((end_t - start_t) * 1000, 2)

            if tc.max_latency_ms and latency_ms > tc.max_latency_ms:
                passed = False
                error_msg = f"Latency {latency_ms}ms exceeded budget {tc.max_latency_ms}ms"

            if passed:
                passed_count += 1

            results.append(TestResult(
                test_id=tc.test_id,
                name=tc.name,
                passed=passed,
                status_code=status,
                latency_ms=latency_ms,
                error_message=error_msg,
                trace=trace_data,
            ))

        total = len(test_cases)
        pass_rate = round((passed_count / total * 100), 2) if total > 0 else 0.0

        return EvaluationReport(
            agent_name=agent_name,
            total_tests=total,
            passed_tests=passed_count,
            failed_tests=total - passed_count,
            pass_rate=pass_rate,
            results=results,
        )


agent_test_harness = AgentTestHarness()
