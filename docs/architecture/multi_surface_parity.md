# Multi-Surface Parity & Testing

The CoReason platform strictly enforces a **Multi-Surface Parity** mandate. This architectural constraint ensures that every platform capability is uniformly accessible, behaves identically, and returns the same data structure regardless of which interaction surface initiates the workflow.

## The Five First-Class Surfaces

The platform exposes five distinct interaction surfaces. None of these surfaces implement business logic; they operate exclusively as thin transport adapters delegating to `src.core.services`.

1. **REST API**: HTTP request/response bindings (FastAPI) for browsers and external services.
2. **CLI**: Command-line interface (`typer`/`click`) for terminal usage and CI/CD pipelines.
3. **MCP Server**: Model Context Protocol JSON-RPC bindings for upstream AI agents and IDEs.
4. **WebSocket / SSE**: Persistent connection adapters for real-time observability and accordion UIs.
5. **Python SDK**: Native in-process programmatic bindings (`CoReasonClient`).

## E2E Workflow Parity Testing

To mathematically prove this parity, our continuous integration suite includes comprehensive integration tests (`test_e2e_surfaces.py`).

### Mocking to Live Integration Pivot

We do not use `unittest.mock` to mock the underlying database for E2E validation. Instead, the testing suite utilizes **Testcontainers** to spin up an ephemeral execution environment on the fly.

- **Ephemeral PostgreSQL Container**: A live `postgres:15-alpine` container is spun up via Testcontainers.
- **Ephemeral Redis Container**: A live `redis:7-alpine` container is spun up to validate WebSocket and Server-Sent Event (SSE) pub/sub streaming logic.

By executing against a real database layer, the E2E parity suite avoids the false-positives common to mocked interfaces and validates true end-to-end integration constraints (such as UUIDv7 primary keys and Tenant ID data isolation).

### Executing Parity Tests

The E2E suite (`tests/test_e2e_surfaces.py`) runs the exact same standard Maker Workflow (e.g., creating a project, triggering an agent build, and exporting the project) through each surface layer individually.

1. **REST Parity**: Verified using `httpx.AsyncClient` invoking the FastAPI endpoints to ensure proper routing and JWT authentication bindings.
2. **CLI Parity**: Verified by executing isolated `subprocess.run(["python", "-m", "src.cli.main"])` commands and asserting JSON return outputs.
3. **SDK Parity**: Verified by invoking the synchronous wrappers provided by `CoReasonClient`.
4. **Service Layer Parity**: Verified by directly `await`ing the core logic methods from `src.core.services`.
5. **MCP Layer Parity**: Verified by executing the FastMCP `@mcp.tool()` handlers directly (e.g., `create_project`, `execute_agent`).
6. **Streaming Layer Parity**: Verified by testing the `pubsub_backplane` logic using a Testcontainers Redis instance.

If any surface yields a different workflow outcome or schema structure, the test suite strictly fails, ensuring the Multi-Surface architectural constraint is preserved.
