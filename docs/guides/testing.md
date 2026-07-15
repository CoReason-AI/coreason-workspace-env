# End-to-End Testing Guide

The CoReason Workspace Environment heavily emphasizes robustness, especially because agent orchestration spans multiple nodes, external integrations, and deterministic state routing. 

To ensure stability across these complex LangGraph architectures, the platform implements a strict **Mock-Free E2E Testing** paradigm.

## Mock-Free Philosophy

Standard unit tests that aggressively mock external dependencies (like the database or LLMs) often fail to catch integration bugs such as JSON decode errors, transaction commit failures, or subtle schema mismatches. 

In CoReason, we prioritize real state interactions:
1. **No Database Mocking**: We do not mock `asyncpg` or the Postgres adapter. Instead, tests utilize a stateful `DummyConnection` and `DummyPool` that actually parse, execute, and store SQL statements in an in-memory dictionary. This exercises the *actual* database adapter code paths (like transaction management and cursor handling) exactly as they run in production.
2. **Deterministic LLM Harness**: Instead of mocking the LLM API layer, we use a `DeterministicTestChatModel`. This subclass perfectly mimics the LangChain/LangGraph LLM interface but deterministically yields structurally perfect `pydantic` output conforming exactly to the tool schemas expected by the graph. This allows the graph to navigate complex map-reduce topologies without brittle prompt-engineering logic during CI/CD.

## Running Tests

To run the full E2E map-reduce testing suite:

```bash
uv run pytest tests/test_e2e_factory.py -v
```

### What happens during this test?

1. The test initializes the `PlatformOrchestrator` pointing to the `factory_ceo` agent.
2. The `stateful_dummy_db` is injected, providing a true SQL-like interface that fully exercises the `PostgresSaver` checkpointer.
3. The orchestrator triggers a massive fan-out task. The `factory_ceo` delegates to the `agent_pm`, which delegates to the `prompt_engineer` and `yaml_compiler`.
4. The `DeterministicTestChatModel` intercepts these tool calls and reliably returns pre-defined, architecturally valid outputs.
5. The map-reduce completes, state is merged back up the tree, and the orchestrator yields the final artifact.
6. The test verifies that the resulting ZIP artifact was actually generated and written to disk.

This ensures that the entire runtime—from the API input, down through the hierarchical agent delegation, to the checkpointer and final artifact generation—is mathematically proven to work.
