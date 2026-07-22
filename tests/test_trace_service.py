import pytest
import time
from src.core.services.trace_service import trace_service

def test_trace_service_lifecycle():
    job_id = "test_job_trace_123"
    
    # 1. Start trace
    trace = trace_service.start_trace(
        job_id=job_id,
        agent_name="factory_ceo",
        user_id="usr_1",
        tenant_id="tnt_1",
        metadata={"env": "test"}
    )
    assert trace.job_id == job_id
    assert trace.status == "running"
    
    # 2. Add span
    t1 = time.time()
    time.sleep(0.01)
    t2 = time.time()
    span = trace_service.add_span(
        job_id=job_id,
        name="prompt_synthesis",
        span_type="llm",
        start_time=t1,
        end_time=t2,
        input_data={"prompt": "build agent"},
        output_data={"result": "ok"}
    )
    assert span is not None
    assert span.name == "prompt_synthesis"
    assert span.duration_ms > 0
    
    # 3. Add step summary
    trace_service.add_step_summary(job_id, "Generated prompt")
    
    # 4. Finish trace
    trace_service.finish_trace(job_id, status="success")
    
    # 5. Retrieve trace
    fetched = trace_service.get_trace(job_id)
    assert fetched is not None
    assert fetched["status"] == "success"
    assert len(fetched["spans"]) == 1
    assert len(fetched["step_summaries"]) == 1
    
    # 6. List traces
    all_traces = trace_service.list_traces(agent_name="factory_ceo")
    assert len(all_traces) >= 1
