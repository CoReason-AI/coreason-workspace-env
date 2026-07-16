import pytest
from langgraph.store.memory import InMemoryStore
from src.core.tools.rag_tools import log_structural_failure, recall_past_failures

@pytest.fixture
def memory_store():
    # Use LangGraph's native InMemoryStore for testing
    return InMemoryStore()

@pytest.mark.asyncio
async def test_log_and_recall_failures(memory_store):
    # 1. Log a failure using the tool
    log_res = await log_structural_failure.ainvoke({
        "code_snippet": "x = 1/0",
        "error_message": "ZeroDivisionError",
        "resolution_hints": "Do not divide by zero.",
        "store": memory_store
    })
    
    assert "Successfully logged structural failure" in log_res
    
    # 2. Recall the failure using the tool
    # InMemoryStore natively supports basic filtering/searching, though it lacks true vector search.
    # It will return the stored items in the namespace.
    recall_res = await recall_past_failures.ainvoke({
        "context_query": "divide",
        "store": memory_store
    })
    
    assert "ZeroDivisionError" in recall_res
    assert "Do not divide by zero." in recall_res
