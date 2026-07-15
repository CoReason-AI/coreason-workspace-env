# Agent Building Standards

> **Scope**: This skill is a construction guide for factory agents that **create** agent definitions. It defines how to structure agent YAMLs, system prompts, and behavioral contracts. It does NOT contain validation checklists — those live in `validation/agent_validation_standards.md`.

---

## 1. Context Engineering Harness

Every agent must fall into exactly one of two categories. No exceptions.

### Orchestrators (`type: supervisor`)

Orchestrators are **state machines** that manage human/agent interaction. They:

- **Evaluate** the user's input against the required data schema
- **Interrogate** the user with targeted, clarifying questions until context is fully saturated
- **Delegate** the saturated context payload to deterministic sub-agents once the threshold is met

Orchestrators MUST NOT:
- Write code or files themselves
- Execute computational tasks directly
- Operate without a clear data schema defining "fully saturated" context

### Sub-Agents (`type: sub-agent`)

Sub-agents are **deterministic workers** that accept fully saturated payloads and execute. They:

- Accept a complete context payload — no missing fields, no ambiguity
- Execute their task (generate files, write prompts, compile YAML, etc.)
- Return execution control with a structured result

Sub-agents MUST NOT:
- Ask the user clarifying questions
- Interrogate the user for missing information
- Make assumptions about missing data — if the payload is incomplete, **fail with a clear error**

### Strict Decoupling Rule

A single `agent.yaml` definition must contain ONLY orchestration logic OR ONLY deterministic execution logic. Never both. If you find yourself adding "ask the user if..." to a sub-agent, or "generate the file..." to an orchestrator, you are violating this rule. Split into two agents.

---

## 2. Namespace and Taxonomy Consistency

- The `name` field in every `agent.yaml` MUST exactly match the `snake_case` name of the folder it resides in
- Example: `src/agents/yaml_compiler/` → `name: "yaml_compiler"`
- This ensures the internal Agent ID matches the namespace and folder routing logic
- No aliases, no overrides, no creative naming

---

## 3. Multi-Surface Parity

Every agent capability must be reachable through all applicable interaction surfaces:

| Surface | Location | Transport |
|---|---|---|
| REST API | `src/api/` | HTTP |
| CLI | `src/cli/` | stdin/stdout |
| MCP Server | `src/mcp/` | JSON-RPC over stdio/SSE |
| WebSocket/SSE | `src/api/streaming/` | Persistent connections |
| Python SDK | `src/sdk/` | In-process |

When producing a new agent, ensure its operations can be invoked from all five surfaces through the shared core service layer (`src/core/`).

---

## 4. Human Escalation

Agents operating in mixed Human-Agent workspaces must:

- Recognize when a decision falls outside their domain or confidence threshold
- Escalate to the human counterpart before proceeding
- Never silently make strategic decisions that a human stakeholder should approve

---

## 5. System Prompt Construction

When writing system prompts for agent YAMLs:

- **Orchestrator prompts** must include: evaluate/interrogate/delegate behavior, data schema reference, escalation paths, and explicit "DO NOT write code yourself" constraint
- **Sub-agent prompts** must include: "DO NOT interrogate the user", "DO NOT ask clarifying questions", deterministic execution constraints, and explicit failure modes for incomplete payloads
- Every prompt must reference the agent's skill dependencies so the agent knows what standards to enforce

## Schema Purity & Data Persistence
1. **God Context Schema Imports**: The coreason-manifest PyPI package is the absolute single source of truth for all schemas. Never duplicate or create local schema files (e.g. ontology.py or state.py). Always import directly from coreason_manifest (e.g., rom coreason_manifest.spec.ontology import CoreasonBaseState).
2. **UUIDv7 Natively**: The environment uses Python 3.14 natively. Always use uuid.uuid7() when generating UUIDs (e.g., for snapshot_id, project_id). Never use uuid.uuid4(). UUIDv7 prevents Postgres B-Tree index fragmentation and provides native chronological sorting.
