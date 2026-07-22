# Core Architecture Principles

The CoReason Workspace Environment implements an opinionated variant of the DeepAgent pattern. While the industry frequently treats multi-agent systems as experimental scripts, this platform enforces a strict Infrastructure as Code (IaC) approach, leveraging deterministic mathematical boundaries rather than heuristic prompting.

## DeepAgent Pattern & Declarative Manifests
Agents within the platform are defined via strictly typed, `pyagentspec`-compatible **YAML manifests**. 
This shift to declarative infrastructure treats agent definitions as portable, version-controlled configurations.

At runtime, a dynamically synthesized **LangGraph StateGraph** node enforces deterministic routing and eliminates deliberation cascades. The `factory_ceo` (instantiated via `create_deep_agent`) dynamically delegates to PMs and workers using standard tool calling and native `deepagents` middleware.

### Strict Version Boundary (deepagents >= 0.6.12)
This platform strictly targets the modern `deepagents >= 0.6.12` API boundaries.
- **Strict `TypedDict` State**: Agent state schemas MUST inherit from `langchain.agents.AgentState` (which is a `TypedDict`). Pydantic models (`BaseModel`) and standard python dataclasses are no longer supported.
- **String-Based System Prompts**: The legacy `SystemPromptConfig` API has been removed. You must pass the system prompt directly as a string to the `system_prompt` argument in `create_deep_agent`.

## The Brain / Body Dichotomy
The platform physically enforces a strict architectural boundary between **Intent** and **Execution** by separating the repository into two primary domains:
- **The Brain (`src/agents/`)**: Represents pure cognitive intent (personas, YAML, StateGraphs) with zero infrastructure code.
- **The Body (`src/core/`)**: The universal runtime harness (PlatformOrchestrator, DB pools, HTTP routers) that mounts the Brain and wires it into the physical world.

## Headless-First Architecture & Dify Integration
The CoReason Workspace Environment is strictly a **Headless Execution Engine**. All stateful conversational UI (chat memory, interactive interrogation, and RAG UI) is fully offloaded to upstream orchestration platforms like **Dify**. 

### The Full-Code Paradigm (Self-Hosted Air-Gapped)
We strictly enforce a **Full-Code** paradigm for building agents. Dify's low-code/no-code drag-and-drop workflow builder is explicitly bypassed. 
- **Build**: All agents are written natively in Python using the `deepagents` SDK and LangGraph inside `src/agents/`.
- **Expose**: The logic is exposed dynamically via the CoReason **MCP Server**.
- **Deploy**: Dify acts exclusively as the **Enterprise Shell**, connecting to the CoReason MCP Server as a tool provider. 

**Critical Security Boundary**: To maintain Data Sovereignty and Zero-Trust, Dify must be **Self-Hosted** (e.g., via local Docker Compose or internal Kubernetes). The CoReason backend is hardcoded to expect an internal Docker network URL (`http://dify-api:5001/v1`). You must never route traffic to Dify's public SaaS cloud (`api.dify.ai`), as this would leak intellectual property across the air-gap boundary. 

*Note on LLMs*: While the orchestration shell (Dify) and execution backend (CoReason) must be self-hosted within your secure perimeter, you may optionally tunnel out to remote Model-as-a-Service (MaaS) providers (e.g., Azure OpenAI, Anthropic, OpenRouter) for inference, provided your enterprise data agreements permit it.

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
- **Physical Sandboxing**: Filesystem paths are strictly validated and pinned to prevent traversal attacks. The environment uses the native `deepagents>=0.6.12` `BackendProtocol` (`StateBackend`) globally to ensure all agents execute structured JSON filesystem tools rather than brittle custom shell tools.

## Multi-Surface Parity
The platform strictly enforces a **Multi-Surface Parity** mandate. This constraint ensures that every platform capability is uniformly accessible, behaves identically, and returns the same data structure regardless of which interaction surface initiates the workflow (REST API, CLI, MCP Server, WebSocket/SSE, Python SDK). None of these surfaces implement business logic; they operate exclusively as thin transport adapters delegating to `src.core.services`.

## Agent Observability & Traceability
To empower upstream AI coding assistants (the "Agent Improvement System") to natively debug and improve the platform's agents, the environment integrates deep, programmable observability exposed directly via the **MCP Server**:
- **State Inspection (Postgres)**: Directly queries the `postgres_checkpointer` to read the exact LangGraph thread checkpoints, enabling deterministic analysis of stuck or failed agent states.
- **LLM Tracing (Langfuse)**: Native Langfuse tracing provides full visibility into the prompts and completions that led to hallucination or validation errors. It natively integrates with LangGraph using the Langfuse CallbackHandler.
- **Dynamic Identity Federation (Vault)**: Supports injecting external API keys securely into the dev HashiCorp Vault at runtime, allowing agents to impersonate dynamic roles without hardcoded secrets.
- **Agent Resumption**: Directly invokes the `PlatformOrchestrator` to seamlessly resume paused or failed agents natively using the LangGraph checkpointer.

All observability logic is encapsulated within `src/core/services/observability_service.py` and strictly obeys the platform's SSOT (Single Source of Truth) configuration, allowing it to transition seamlessly from local development into enterprise Kubernetes clusters without hardcoded topology strings.
## IANA Private Enterprise Number (PEN 66197) URN Authority & Module Catalog

The platform operates an official URN Authority backed by Coreason AI's IANA PEN assignment **66197**:
- **Official IANA OID URN**: `urn:oid:1.3.6.1.4.1.66197:<resource_type>:<resource_id>`
- **Coreason URL Authority**: `https://urn.coreason.ai/1.3.6.1.4.1.66197/<resource_type>/<resource_id>`

Every project, agent, skill, workflow, and custom component synthesized by the factory is assigned a global, unique URN under PEN 66197. The platform provides a persistent, scalable `CatalogService` and LangGraph tools (`search_catalog_tool`, `resolve_urn_tool`, `import_catalog_module_tool`) allowing human operators and building agents (`factory_ceo`, `librarian_pm`) to:
1. Search past projects and exemplars by query or tag.
2. Resolve OID URNs or Coreason URLs to inspect full metadata and source specifications.
3. Import complete project templates or individual agent modules directly into target project spaces.

## Sandboxed Environment Deployments (E2B / Isolated Containers)

To allow building agents and human teams to test and execute agentic applications safely in multi-tenant project spaces, the platform provides `SandboxService`:
- Provisions isolated execution sandboxes with pre-bound secrets, credentials, database connections, and MCP tool servers.
- Fully exposed across all 5 interaction surfaces (`/sandboxes` REST API, `sandbox` CLI, MCP tools, Python SDK).

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
- **Physical Sandboxing**: Filesystem paths are strictly validated and pinned to prevent traversal attacks. The environment uses the native `deepagents>=0.6.12` `BackendProtocol` (`StateBackend`) globally to ensure all agents execute structured JSON filesystem tools rather than brittle custom shell tools.

## Multi-Surface Parity
The platform strictly enforces a **Multi-Surface Parity** mandate. This constraint ensures that every platform capability is uniformly accessible, behaves identically, and returns the same data structure regardless of which interaction surface initiates the workflow (REST API, CLI, MCP Server, WebSocket/SSE, Python SDK). None of these surfaces implement business logic; they operate exclusively as thin transport adapters delegating to `src.core.services`.

## Agent Observability & Traceability
To empower upstream AI coding assistants (the "Agent Improvement System") to natively debug and improve the platform's agents, the environment integrates deep, programmable observability exposed directly via the **MCP Server**:
- **State Inspection (Postgres)**: Directly queries the `postgres_checkpointer` to read the exact LangGraph thread checkpoints, enabling deterministic analysis of stuck or failed agent states.
- **LLM Tracing (Langfuse)**: Native Langfuse tracing provides full visibility into the prompts and completions that led to hallucination or validation errors. It natively integrates with LangGraph using the Langfuse CallbackHandler.
- **Dynamic Identity Federation (Vault)**: Supports injecting external API keys securely into the dev HashiCorp Vault at runtime, allowing agents to impersonate dynamic roles without hardcoded secrets.
- **Agent Resumption**: Directly invokes the `PlatformOrchestrator` to seamlessly resume paused or failed agents natively using the LangGraph checkpointer.

All observability logic is encapsulated within `src/core/services/observability_service.py` and strictly obeys the platform's SSOT (Single Source of Truth) configuration, allowing it to transition seamlessly from local development into enterprise Kubernetes clusters without hardcoded topology strings.

## Zero-Waste Ambient Telemetry (Open-Source First)
The orchestrator maintains rigorous Request-Scoped Telemetry across thousands of asynchronous nodes without leaking memory and without custom `weakref` boilerplate. It achieves this by strictly adopting the CNCF standard **OpenTelemetry Context** (`opentelemetry.context`) and **Structlog ContextVars** natively. 

Standard `logging` instances (used by third parties like Langchain or FastAPI) are transparently hijacked and pipelined through `structlog`. At the entry point of any orchestrator execution, the unique `session_id` is bound to the ambient context. Every deeply nested API call, database query, and model invocation automatically inherits this tracing ID gracefully, providing 100% causal visibility in Langfuse (or any OTel backend) without manually polluting function signatures.

## Developer Considerations & Known Issues

When working on the integration layer between the CoReason backend and the Dify orchestration shell, developers should be aware of the following resolved architectural gotchas:

- ❌ **Broken Dify Webhook (POST /mcp/sync)**: Code in `agent_service.py` previously attempted to call `{settings.DIFY_API_URL}/mcp/sync` to automatically sync tool providers upon deployment. **Standard Dify has no `/mcp/sync` endpoint (returns 404)**. We have deprecated this logic; developers must now manually click 'Refresh' on the CoReason MCP Tool inside the Dify UI to reflect new agents.
- ❌ **Swallowing HTTP Errors**: `agent_service.py` previously caught exceptions on Dify API calls but did not call `response.raise_for_status()`, returning a fake `status: success` or `status: running` even when HTTP requests failed (e.g., 500 Internal Server Error). This has been patched to strictly enforce robust async exponential backoff for transient errors, while immediately bubbling deterministic errors as a sanitized `status: error` JSON payload to protect upstream clients from raw stack traces.
- ❌ **Unauthenticated SSE Transport**: Previously, `src/mcp/server.py` ran the FastMCP SSE endpoint without any authorization, leaving the MCP surface completely open on the internal network. We have patched this by adding a Starlette `BearerAuthMiddleware` that enforces Bearer token validation natively. Upstream clients (like Dify) must now inject `Authorization: Bearer <TOKEN>` where the token matches the `MCP_API_KEY` environment variable. If `MCP_API_KEY` is not set, the MCP server will proactively crash on startup in `sse` mode to prevent fail-open vulnerabilities.

## Agent-to-Agent (A2A) Communication Protocol

The platform implements a dual-tier **Agent-to-Agent (A2A)** communication protocol built natively on `deepagents`, `LangGraph`, and `LangChain`.

### Tier 1: Intra-Sandbox A2A Protocol (In-Process LangGraph Subagent Tools)
Within a single OpenShell sandbox container workspace (`sandboxes/<sandbox_id>`), parent orchestrators (`factory_ceo`) communicate with child agents (`agent_pm`, `librarian_pm`, `research_agent`) in-process:
- **Harness**: Native `deepagents.graph.create_deep_agent` with subagent middleware (`deepagents.middleware.subagents`).
- **State Model**: `DeepAgentState` (inheriting from `langchain.agents.AgentState` `TypedDict`).
- **Control Flow**: Direct LangGraph `StateGraph` node traversal. Subagents return execution payloads via `Command(resume=...)` or direct state dictionaries.
- **Identity**: Bound by local Python namespace and IANA PEN 66197 OID URN (`urn:oid:1.3.6.1.4.1.66197:agent:<name>`).

### Tier 2: Inter-Sandbox A2A Protocol (Remote LangChain FastMCP JSON-RPC)
When communicating across distinct OpenShell sandboxes, physical containers, or multi-tenant network boundaries:
- **Transport**: `FastMCP` JSON-RPC over HTTP/stdio on port `9005`.
- **LangChain Integration**: `langchain_mcp_adapters` dynamically binds remote MCP agent endpoints as native `LangChain` tool objects (`StructuredTool`).
- **Security Boundary**: Governed by the caller and callee's OpenShell `openshell.policy.json` egress whitelist (`allowed_egress_domains`, `mcp_server_ports: [9005]`).
- **URN Resolution**: Agents resolve remote targets using `CatalogService` via `urn:oid:1.3.6.1.4.1.66197:agent:<id>` or `https://urn.coreason.ai/...`.

### Deep Context, Memory & State Transfer Mechanics
The A2A protocol enforces 3 distinct state and memory transfer layers:
1. **Checkpointed LangGraph State (`AsyncPostgresSaver`)**:
   - Every agent execution graph is backed by PostgreSQL checkpointers.
   - When Agent A delegates to Agent B, full step history, tool invocations, messages, and `DeepAgentState` dictionary keys are preserved with 100% loss-free state fidelity across thread checkpoints.
2. **Progressive Disclosure Deep Context (Lazy Artifact Loading)**:
   - To prevent context window saturation and prompt degradation during multi-hop delegation, heavy artifacts (large source codebases, database schemas, vector indices) are passed as URI references (`file:///...` or `urn:oid:1.3.6.1.4.1.66197:...`).
   - The receiving subagent lazy-loads deep context on-demand using native `deepagents` `StateBackend` filesystem tools.
3. **Persistent Episodic & Semantic Memory**:
   - Cross-session memory is persisted in PostgreSQL and Qdrant vector indices via `src/core/services/memory_service.py`.
   - Subagents automatically query relevant past project memories, architectural decisions, and error traces during delegated task execution.

