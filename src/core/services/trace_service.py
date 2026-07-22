import time
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid

logger = logging.getLogger(__name__)


class SpanRecord(BaseModel):
    span_id: str = Field(default_factory=lambda: str(uuid.uuid7()))
    name: str
    span_type: str = Field(description="'llm', 'tool', 'agent_step', or 'task'")
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ExecutionTrace(BaseModel):
    job_id: str
    agent_name: str
    user_id: str
    tenant_id: str
    start_time: float
    end_time: Optional[float] = None
    status: str = Field(default="running")  # running, success, error
    spans: List[SpanRecord] = Field(default_factory=list)
    step_summaries: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TraceService:
    """
    Manages execution trace capturing, indexing, and retrieval.
    Enables meta-programming: agents building agents can inspect traces of target executions.
    """

    def __init__(self):
        self._traces: Dict[str, ExecutionTrace] = {}

    def start_trace(self, job_id: str, agent_name: str, user_id: str, tenant_id: str, metadata: Optional[Dict[str, Any]] = None) -> ExecutionTrace:
        trace = ExecutionTrace(
            job_id=job_id,
            agent_name=agent_name,
            user_id=user_id,
            tenant_id=tenant_id,
            start_time=time.time(),
            metadata=metadata or {}
        )
        self._traces[job_id] = trace
        logger.info(f"Started execution trace for job {job_id} ({agent_name})")
        return trace

    def add_span(
        self,
        job_id: str,
        name: str,
        span_type: str,
        start_time: float,
        end_time: float,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> Optional[SpanRecord]:
        trace = self._traces.get(job_id)
        if not trace:
            logger.warning(f"Attempted to add span to non-existent trace {job_id}")
            return None

        duration_ms = round((end_time - start_time) * 1000, 2)
        span = SpanRecord(
            name=name,
            span_type=span_type,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            input_data=input_data or {},
            output_data=output_data,
            error=error
        )
        trace.spans.append(span)
        return span

    def add_step_summary(self, job_id: str, summary: str):
        trace = self._traces.get(job_id)
        if trace:
            trace.step_summaries.append(summary)

    def finish_trace(self, job_id: str, status: str = "success", error: Optional[str] = None):
        trace = self._traces.get(job_id)
        if trace:
            trace.end_time = time.time()
            trace.status = status
            if error:
                trace.metadata["error"] = error
            logger.info(f"Finished trace for job {job_id} with status {status}")

    def get_trace(self, job_id: str) -> Optional[Dict[str, Any]]:
        trace = self._traces.get(job_id)
        return trace.model_dump() if trace else None

    def list_traces(self, agent_name: Optional[str] = None) -> List[Dict[str, Any]]:
        results = []
        for t in self._traces.values():
            if agent_name is None or t.agent_name == agent_name:
                results.append(t.model_dump())
        return results


trace_service = TraceService()
