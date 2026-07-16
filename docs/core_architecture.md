# Core Architecture Principles

The CoReason Workspace Environment implements an opinionated variant of the DeepAgent pattern. While the industry frequently treats multi-agent systems as experimental scripts, this platform enforces a strict Infrastructure as Code (IaC) approach, leveraging deterministic mathematical boundaries rather than heuristic prompting.

## DeepAgent Pattern & Declarative Manifests
Agents within the platform are not instantiated via complex, hardcoded Python boilerplate. Instead, they are defined via strictly typed, `pyagentspec`-compatible **YAML manifests**. 
This shift to declarative infrastructure treats agent definitions as portable, version-controlled configurations.

At runtime, a specialized YAML compiler reads the agent manifest and dynamically synthesizes an executable **LangGraph StateGraph** node, enforcing deterministic routing and eliminating deliberation cascades.

## The Brain / Body Dichotomy
The platform physically enforces a strict architectural boundary between **Intent** and **Execution** by separating the repository into two primary domains:
- **The Brain (`src/agents/`)**: Represents pure cognitive intent (personas, YAML, StateGraphs) with zero infrastructure code.
- **The Body (`src/core/`)**: The universal runtime harness (PlatformOrchestrator, DB pools, HTTP routers) that mounts the Brain and wires it into the physical world.

## Context Engineering & Schema Saturation
Context Engineering is the practice of treating context assembly as a disciplined, mathematical control plane *prior* to kinetic execution. Before any deterministic worker node is activated, a supervisory routing node actively interrogates the user's input or the incoming API payload against a predefined `Pydantic` schema. 

This pre-dispatch **Schema Saturation** acts as a programmatic choke point. Only when the target schema achieves 100% saturation is the payload released to specialized sub-agents.

## Maker-Checker-Approver Pipeline
The platform completely rejects stochastic self-correction (Generator-Critic) for structural and syntactical validation. Instead, it enforces a rigid **Maker-Checker-Approver** pipeline:
1. **The Maker (Generation)**: Generates the required artifact (Python, JSON, SQL).
2. **The Checker (Deterministic Validation)**: Intercepts the artifact with a purely deterministic LangGraph node containing zero generative LLM calls. It runs AST parsers (`libcst`), strict Pydantic checks, and sandboxed code execution. *Note: AST manipulation by Maker agents is strictly forbidden, as parsers instantly fail on syntactically invalid files, paralyzing the agent. Maker agents must use language-agnostic string replacement, while the Checker uses AST tools purely for read-only structural validation.*
3. **Remediation / Approver**: Artifacts failing the Checker are routed back to the Maker. Passing artifacts proceed to an Approver (PM or Governance Agent). The Governance Agent implements **Multi-Model Consensus** by invoking an LCEL-based evaluation pipeline across multiple test-time compute profiles. If the consensus score fails, the Approver strictly enforces **Dialectical Synthesis** (generating an explicit Thesis, Antithesis, and Synthesis) to construct mathematically rigorous feedback before routing back to the Maker for remediation.

## Anti-Stub Enforcement Policy
The platform operates under a strict **No-Mock, Anti-Stub Policy**. The words `mock`, `stub`, `fake`, and `simulate` are completely banned from all execution and orchestration paths. Every agent must fulfill a genuine structural role using real LLM invocations, real DB checkpointers, and authentic integrations.

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
- **LLM Tracing (Langfuse)**: Programmatically fetches execution traces from the local Langfuse API, providing full visibility into the prompts and completions that led to hallucination or validation errors. It natively integrates with LangGraph using `langfuse.callback`.
- **Dynamic Identity Federation (Vault)**: Supports injecting external API keys securely into the dev HashiCorp Vault at runtime, allowing agents to impersonate dynamic roles without hardcoded secrets.
- **Agent Resumption**: Directly invokes the `PlatformOrchestrator` to seamlessly resume paused or failed agents natively using the LangGraph checkpointer.

All observability logic is encapsulated within `src/core/services/observability_service.py` and strictly obeys the platform's SSOT (Single Source of Truth) configuration, allowing it to transition seamlessly from local development into enterprise Kubernetes clusters without hardcoded topology strings.
