# Core Architecture Principles

The CoReason Workspace Environment implements an opinionated variant of the DeepAgent pattern. While the industry frequently treats multi-agent systems as experimental scripts, this platform enforces a strict Infrastructure as Code (IaC) approach, leveraging deterministic mathematical boundaries rather than heuristic prompting.

## DeepAgent Pattern & Declarative Manifests
Agents within the platform are defined via strictly typed, `pyagentspec`-compatible **YAML manifests**. 
This shift to declarative infrastructure treats agent definitions as portable, version-controlled configurations.

At runtime, a dynamically synthesized **LangGraph StateGraph** node enforces deterministic routing and eliminates deliberation cascades. The `factory_ceo` (instantiated via `create_deep_agent`) dynamically delegates to PMs and workers using standard tool calling and native `deepagents` middleware.

## The Brain / Body Dichotomy
The platform physically enforces a strict architectural boundary between **Intent** and **Execution** by separating the repository into two primary domains:
- **The Brain (`src/agents/`)**: Represents pure cognitive intent (personas, YAML, StateGraphs) with zero infrastructure code.
- **The Body (`src/core/`)**: The universal runtime harness (PlatformOrchestrator, DB pools, HTTP routers) that mounts the Brain and wires it into the physical world.

## Context Engineering & Schema Saturation
Context Engineering is the practice of treating context assembly as a disciplined, mathematical control plane *prior* to kinetic execution. Before any deterministic worker node is activated, a supervisory routing node actively interrogates the user's input or the incoming API payload against a predefined `Pydantic` schema. 

This pre-dispatch **Schema Saturation** acts as a programmatic choke point. Only when the target schema achieves 100% saturation is the payload released to specialized sub-agents.

## Anti-Stub Enforcement Policy
The platform operates under a strict **No-Mock, Anti-Stub Policy**. The words `mock`, `stub`, `fake`, and `simulate` are completely banned from all execution and orchestration paths. Every agent must fulfill a genuine structural role using real LLM invocations, real DB checkpointers, and authentic integrations.
For example, the project and database interactions are enforced as true integrations using genuine Postgres connection pools (`psycopg_pool.AsyncConnectionPool`) and real tracing (`src/core/services/observability_service.py`), completely eliminating hollow stubs that might mask underlying integration failures.



## The Epistemic Firewall (Zero-Trust RAG)
Generative language models are mathematically forbidden from executing direct queries against high-entropy raw data lakes or unverified external APIs. 
The platform introduces a multi-stage cryptographic pipeline:
- Data chunks are extracted and cryptographically signed (e.g., Ed25519).
- Sub-routines retrieve data and verify the cryptographic signature.
- Valid data is wrapped in a strongly typed `KnowledgeReceipt` and securely injected into the agent's context.

## Enterprise Runtime
To operate in production, the environment implements:
- **High-Performance Asynchronous Execution**: Non-blocking async IO (`psycopg_pool.AsyncConnectionPool`) preventing thread bottlenecks during agent DAG execution.
- **True Multi-Tenant Data Isolation**: LangGraph checkpoint threads do not use the `public` schema. Each project is dynamically mapped to a dedicated schema (e.g., `project_{uuid}`).
- **Physical Sandboxing**: Filesystem paths are strictly validated and pinned to prevent traversal attacks.

## Multi-Surface Parity
The platform strictly enforces a **Multi-Surface Parity** mandate. This constraint ensures that every platform capability is uniformly accessible, behaves identically, and returns the same data structure regardless of which interaction surface initiates the workflow (REST API, CLI, MCP Server, WebSocket/SSE, Python SDK). None of these surfaces implement business logic; they operate exclusively as thin transport adapters delegating to `src.core.services`.

## Agent Observability & Traceability
To empower upstream AI coding assistants (the "Agent Improvement System") to natively debug and improve the platform's agents, the environment integrates deep, programmable observability exposed directly via the **MCP Server**:
- **State Inspection (Postgres)**: Directly queries the `postgres_checkpointer` to read the exact LangGraph thread checkpoints, enabling deterministic analysis of stuck or failed agent states.
- **LLM Tracing (LangSmith)**: Native LangChain tracing provides full visibility into the prompts and completions that led to hallucination or validation errors. It natively integrates with LangGraph using the `LANGCHAIN_TRACING_V2` environment variables.
- **Dynamic Identity Federation (Vault)**: Supports injecting external API keys securely into the dev HashiCorp Vault at runtime, allowing agents to impersonate dynamic roles without hardcoded secrets.
- **Agent Resumption**: Directly invokes the `PlatformOrchestrator` to seamlessly resume paused or failed agents natively using the LangGraph checkpointer.

All observability logic is encapsulated within `src/core/services/observability_service.py` and strictly obeys the platform's SSOT (Single Source of Truth) configuration, allowing it to transition seamlessly from local development into enterprise Kubernetes clusters without hardcoded topology strings.

## Zero-Waste Ambient Telemetry (Open-Source First)
The orchestrator maintains rigorous Request-Scoped Telemetry across thousands of asynchronous nodes without leaking memory and without custom `weakref` boilerplate. It achieves this by strictly adopting the CNCF standard **OpenTelemetry Context** (`opentelemetry.context`) and **Structlog ContextVars** natively. 

Standard `logging` instances (used by third parties like Langchain or FastAPI) are transparently hijacked and pipelined through `structlog`. At the entry point of any orchestrator execution, the unique `session_id` is bound to the ambient context. Every deeply nested API call, database query, and model invocation automatically inherits this tracing ID gracefully, providing 100% causal visibility in LangSmith (or any OTel backend) without manually polluting function signatures.
