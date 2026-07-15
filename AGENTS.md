# CoReason Workspace Environment: Agent Customizations & Rules

**Platform Identity:**
`coreason-workspace-env` is an **agent-building factory**. It is a LangGraph DeepAgent-based, multi-user, project-oriented, opinionated platform where humans and AI agents collaborate to design, build, test, and deploy opinionated agentic platforms — each seamlessly deployable as MCP servers (Model Context Protocol). The platform is "opinionated" because it natively enforces the DeepAgent LangGraph pattern: every agent is strictly defined via a YAML manifest, strictly isolated to one agent per folder, and converted via PyAgentSpec into LangGraph execution nodes.

**What you are building and maintaining:**
You are co-building an agent factory with a human partner. The factory is staffed by a hierarchy of agents (`factory_ceo` → PMs → workers like `prompt_engineer` and `yaml_compiler`) that collectively design, validate, and compile agent definitions for downstream platforms. Your job is to maintain and evolve both the factory infrastructure and the factory agents themselves.

**Two-Layer Rule Propagation:**
The rules in this file govern **you** — the AI coding assistant editing this repository. But the factory agents (`factory_ceo`, `agent_pm`, `prompt_engineer`, `yaml_compiler`) are the ones that actually *produce* agent definitions at runtime. They have their own authoritative references — the shared skills library at `src/core/skills/`, split into **building** standards (for Makers) and **validation** standards (for the Checker). These two layers must stay in sync:

| Layer | Audience | Location | Purpose |
|---|---|---|---|
| **AGENTS.md** (this file) | AI coding assistants (you) | Repo root | Governs how you write and modify code in this repo |
| **Building standards** | Factory Maker agents at runtime | `src/core/skills/building/` | Governs how factory agents construct artifacts (agents, MCPs, skills, workflows, diagrams) |
| **Validation standards** | `agent_validator` at runtime | `src/core/skills/validation/` | Governs how the Checker validates artifacts before disk write — formal pass/fail checklists |

The factory operates a **Maker-Checker-Approver** pipeline: builders (yaml_compiler, prompt_engineer) produce artifacts → `agent_validator` checks them against validation standards → `agent_pm` approves or routes back for remediation.

When you update a rule in this file, ask yourself: *does the corresponding building standard AND/OR validation standard also need to be updated?* Keep all three layers aligned.

## DeepAgent Context Engineering Principles

When creating or modifying agents within this platform (specifically in `src/agents/`), you must adhere to the **Context Engineering Harness** philosophy:

1. **State Machine Orchestrators**: Primary orchestrators should not execute tasks statically. They must act as state machines that:
   - **Evaluate**: Actively measure the user's input against the required data schema.
   - **Interrogate**: Loop with the user (asking targeted, clarifying questions) until the context is fully saturated.
   - **Delegate**: Once the internal context threshold is met, stop talking to the user and instantly delegate the raw context payload to a specialized sub-agent.

2. **Deterministic Sub-Agents**: Sub-agents (like compilers or generators) should operate deterministically. They do NOT interrogate the user. They accept fully saturated context payloads from the Orchestrator, execute the computational or destructive task (e.g., writing files), and return execution control.

3. **Strict Decoupling**: Never mix user-interrogation logic with deterministic generation logic in the same agent YAML definition.

4. **Namespace and Taxonomy Consistency**: The `name` field in every `agent.yaml` MUST exactly match the `snake_case` name of the folder it resides in (e.g., `src/agents/project_initiation/` means the YAML name must be `project_initiation`). This strictly ensures the internal Agent ID perfectly matches the namespace and folder routing logic.

## Multi-Surface Interaction Parity

The platform exposes **five first-class interaction surfaces**. Every platform capability must be reachable through all applicable surfaces. This is a non-negotiable architectural constraint.

### Interaction Surfaces

| Surface | Location | Consumer | Transport |
|---|---|---|---|
| **REST API** | `src/api/` | Browsers, scripts, external services | HTTP request/response |
| **CLI** | `src/cli/` | Terminals, CI/CD pipelines, air-gapped environments | stdin/stdout |
| **MCP Server** | `src/mcp/` | AI agents, IDEs, upstream orchestrators | MCP (JSON-RPC over stdio/SSE) |
| **WebSocket / SSE** | `src/api/streaming/` | Real-time dashboards, agent UIs | Persistent connections |
| **Python SDK** | `src/sdk/` | Programmatic embedding (`import coreason`) | In-process |

### Rules

1. **Shared Core Logic**: All five surfaces are thin transport adapters over the same core service layer (`src/core/`). Business logic must never be duplicated across surfaces. A capability exists in `src/core/` first, and each surface wraps it.

2. **Full Surface Coverage**: When a new core capability is added, corresponding bindings must be created across all applicable surfaces in the same PR/changeset. Not every capability maps to every surface (e.g., streaming-only events don't need a CLI command), but the default assumption is full coverage unless explicitly justified.

3. **Schema Consistency**: All surfaces must return the same data schema for equivalent operations. The CLI outputs structured JSON by default (parseable by scripts and upstream agents) with an optional `--pretty` flag for human-readable formatting. The MCP server exposes the same schemas as tool input/output definitions.

4. **Headless-First Design**: The platform must be fully operable without a browser. Any workflow achievable through the Swagger UI must be equally achievable through CLI commands and MCP tool calls. This ensures usability in air-gapped, CI/CD, terminal-only, and agent-to-agent environments.

5. **MCP-Native Identity**: Since this platform builds systems that are *deployable as MCPs*, the platform itself must be consumable as an MCP server. Every agent, project operation, and administrative action should be exposed as MCP tools so upstream AI agents and IDEs can orchestrate the platform natively.

6. **Real-Time Observability**: Long-running agent executions must stream progress via WebSocket/SSE. The CLI, SDK, and MCP surfaces must all be able to subscribe to these streams for their respective consumers (CLI prints incremental lines, SDK yields async iterators, MCP emits progress notifications).

## Schema Purity & Data Persistence
1. **God Context Schema Imports**: The coreason-manifest PyPI package is the absolute single source of truth for all schemas. Never duplicate or create local schema files (e.g. ontology.py or state.py). Always import directly from coreason_manifest (e.g., rom coreason_manifest.spec.ontology import CoreasonBaseState).
2. **UUIDv7 Natively**: The environment uses Python 3.14 natively. Always use uuid.uuid7() when generating UUIDs (e.g., for snapshot_id, project_id). Never use uuid.uuid4(). UUIDv7 prevents Postgres B-Tree index fragmentation and provides native chronological sorting.
