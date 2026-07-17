# CoReason Testing Framework 🧪

Welcome to the **CoReason Workspace Environment** testing guide. This repository enforces strict, enterprise-grade testing paradigms, notably the **"Zero Mock"** architecture.

## 🏗️ Zero Mock Architecture

We do not use `unittest.mock` to stub out external infrastructure (like databases) because mocks rapidly drift from reality in production, hiding integration bugs. Instead, our tests are executed against **real, ephemeral infrastructure**.

We achieve this via `testcontainers`, which programmatically spins up isolated Docker containers (e.g., PostgreSQL Checkpointer, Langfuse telemetry server) for the lifetime of the test session.

> [!WARNING]
> Because of our "Zero Mock" requirement, **Docker Desktop (or an equivalent daemon) MUST be running locally** before you can execute the test suite. If Docker is not running, the End-to-End (E2E) tests will hang or fail.

## 🛠️ Prerequisites & Troubleshooting

### Windows / Docker Desktop
When running `testcontainers` on Windows, you may occasionally experience hangs or port-binding conflicts if Docker Desktop becomes unresponsive.

**Troubleshooting Tips:**
1. **Docker is hanging on test start**: Run `docker ps` to see if orphaned `testcontainers` instances are stuck. Use `docker stop $(docker ps -aq)` to clear them.
2. **Port Exhaustion**: Our global Pytest fixture (`global_postgres_container` in `tests/conftest.py`) limits instantiation to `scope="session"`, spinning up a single DB container for the entire suite. If a test manually spins up a container and crashes, it might leak ports.
3. **Ensure Docker is Running**: Ensure the Docker Engine icon is green before running `coreason test`.

## 🚀 Running Tests

### Option 1: The Headless CLI (Recommended)

In accordance with our "Agent-First CLI" mandate, we have built a wrapper command that handles execution and formatting for you.

```bash
# Run all tests natively
uv run coreason test

# Run tests and generate a coverage report
uv run coreason test --coverage

# Run strictly End-to-End tests
uv run coreason test --e2e
```

### Option 2: The Raw Pytest Interface

If you need granular control, you can invoke the underlying `pytest` command directly using `uv`.

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src

# Run a specific test file
uv run pytest tests/test_e2e_surfaces.py -v
```

> [!TIP]
> If you are contributing new features or modifying the Agent logic, you MUST run tests with `--coverage`. Our PR policy strictly rejects any code that drops the project's coverage threshold.

## 🏭 The 10-Step Real-World E2E Scenario

To guarantee our architecture handles real-world usage, the End-to-End tests in `tests/test_e2e_surfaces.py` and `tests/test_e2e_factory.py` strictly validate the following 10-step Agent Factory lifecycle:

1. **Project Creation**: A new tenant workspace is initialized.
2. **Infrastructure Bootstrapping**: Dedicated local telemetry (Langfuse) and Checkpointer schemas are initialized.
3. **Intent Injection**: The user sends an ambiguous domain intent (e.g., `"build a clinical trial platform"`) to the `factory_ceo` Orchestrator.
4. **State Machine Interrogation**: The `factory_ceo` evaluates the context. If underspecified, it loops back to interrogate the human via the CLI prompt handler.
5. **Worker Delegation**: Once saturated, the CEO deterministically delegates the context payload to standard background workers (like the `yaml_compiler`).
6. **Artifact Compilation**: The worker agents generate strict YAML manifests matching the `snake_case` routing taxonomy.
7. **Native Finalization**: The generated artifacts are compiled and synchronized natively via `deepagents` middleware and state routing (eliminating brittle AST validation).
8. **Multi-Agent Consensus**: The PM agent approves the final state and finalizes the agent definitions.
9. **Streaming Accordion UX**: Throughout steps 3-8, all state mutations and tool calls are piped over a persistent Server-Sent Events (SSE) socket and rendered in real-time.
10. **Platform Export**: The finished, fully-compiled multi-agent workspace is archived and exported as a deployable system (`workspace.tar.gz`).

All testing surfaces (REST API, Python SDK, CLI, and MCP) MUST successfully execute this exact 10-step flow identically.
