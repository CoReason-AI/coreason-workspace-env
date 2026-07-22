# Developer Guide: Extending & Testing the Platform

This guide outlines how to extend the CoReason Workspace Environment with custom skills, and test your agent architectures.

## 1. Building Skills

An agent's capabilities are extended through modular, progressively disclosed **Skills**. Skills encapsulate complex workflows, domain knowledge, or specific tool integrations into strictly-typed, atomic Python `@tools`. 

### Skill Architecture
Skills are stored in the shared library at `src/core/skills/`. They are functionally split:
- `src/core/skills/building/`: Standards and execution tools for worker agents.

A standard skill directory contains:
```text
skills/<skill_name>/
├── SKILL.md            # Required: Core instructions and metadata
├── scripts/            # Helper Python scripts for deterministic execution
├── examples/           # Reference implementations
└── references/         # Extended documentation
```

### The SKILL.md File
The `SKILL.md` file is the absolute source of truth. It contains YAML frontmatter and a Markdown body.
- **Frontmatter**: The `name` and `description` are critical for Progressive Disclosure.
- **Body**: The Markdown body contains specific instructions the agent will read *after* triggering the skill. Keep under 500 lines.

### Core Mandates
1. **Atomic Scope**: The skill must adhere to the Single Responsibility Principle.
2. **Transactional Safety**: If the skill manipulates data, it must be idempotent or utilize Write-Ahead Logging (WAL).
3. **Centralized Pydantic Ontology**: All schemas, models, and agent state geometries must be imported centrally from `src.core.ontology`. Never create local schema definitions inside individual agent directories.
4. **Deterministic Governance**: The skill executes deterministically in Python, acting as a bumper for the stochastic LLM.

## 2. End-to-End Testing

To ensure stability across complex LangGraph architectures, the platform implements a strict **Mock-Free E2E Testing** paradigm.

### Mock-Free Philosophy
1. **No Database Mocking**: Tests utilize ephemeral local databases provisioned by standard pytest fixtures (or a local dev backend). We run queries against real database engines without mocks or stubs, ensuring the exact ORM and execution paths are validated natively.
2. **Native LangChain v1 Agents**: We test against authentic `create_deep_agent` graphs instead of deprecated `AgentExecutor` constructs, verifying modern state routing natively.
3. **Open-Source First Decoupling**: Models are dynamically loaded via Langchain's `init_chat_model` rather than hardcoding proprietary SDKs (like `ChatOpenAI`), ensuring enterprise fallback to local VLLM/Ollama deployments without altering source code.
4. **Structured Filesystem Isolation**: Instead of writing brittle custom tools using `os` and `glob`, agents must strictly rely on the native `BackendProtocol` tools (`StateBackend`) injected globally into `deepagents>=0.6.12`, providing isolated and structured virtual filesystem actions.

### Running Tests
To run the full E2E testing suite against the live orchestrators natively:
```bash
uv run coreason test --e2e
```

This ensures the entire runtime—from API input, down through hierarchical agent delegation, to the checkpointer and final artifact generation—is mathematically proven to work.

## 3. Local Development Topologies

When building or testing locally, you can choose how much of the stack you want to run on your own hardware versus relying on cloud endpoints.

### Local Only
The easiest way to spin this up locally without any external dependencies is via Docker Compose using the Standalone override. This configuration natively spins up **MinIO** for S3-compatible local storage and **Ollama** for local LLM inference (requires an NVIDIA GPU). It bypasses remote images and builds the workspace directly from source.

```bash
docker compose -f docker-compose.yaml -f docker-compose.standalone.yaml up -d --build
```

> [!IMPORTANT]
> **Ollama Setup:** The first time you launch the standalone stack, you must pull the model manually by executing into the container:
> `docker compose -f docker-compose.yaml -f docker-compose.standalone.yaml exec ollama ollama run llama3`

This automatically spins up the `platform_server`, `postgres_checkpointer`, `vault`, `jaeger`, `minio`, and `ollama` components. 

### Hybrid
For standard development using cloud-hosted models (e.g., OpenAI, OpenRouter) and public S3 endpoints, you can avoid spinning up local AI models by using the base compose file:

```bash
docker compose up -d
```

This will run the core state infrastructure (Postgres, Vault, Jaeger) locally, but relies on the `LLM_BASE_URL` and `WORM_S3_ENDPOINT` variables in your `.env` file to route traffic to the cloud.
