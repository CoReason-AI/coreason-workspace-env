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
1. **No Database Mocking**: Tests utilize a stateful `DummyConnection` and `DummyPool` that actually parse and store SQL statements in an in-memory dictionary.
2. **Native LangChain v1 Agents**: We test against authentic `create_agent` graphs instead of deprecated `AgentExecutor` constructs, verifying modern state routing natively.
3. **Open-Source First Decoupling**: Models are dynamically loaded via Langchain's `init_chat_model` rather than hardcoding proprietary SDKs (like `ChatOpenAI`), ensuring enterprise fallback to local VLLM/Ollama deployments without altering source code.

### Running Tests
To run the full E2E testing suite, we rely on the native DeepAgents hierarchical routing flow:
```bash
uv run pytest tests/test_integration.py -v
```

This ensures the entire runtime—from API input, down through hierarchical agent delegation, to the checkpointer and final artifact generation—is mathematically proven to work.

## 3. Agent Tool Authorization (OPA)

Permissions within the platform are completely decoupled from Python code via **Open Policy Agent (OPA)**. 

### Writing Native Tools (No Decorators)
When writing a new tool, developers do **not** need to add custom Python decorators (e.g., `@opa_enforced`) or hardcoded `if user_role == "..."` logic into their `@tool` functions. 

The platform intercepts the native LangChain `on_tool_start` event globally via the `OPAAuthzCallbackHandler`. If an agent lacks permission, the handler catches it, raises a standard `ToolException`, and safely returns "Permission Denied" to the LLM without crashing the orchestrator.

### Writing Policies
To authorize a new tool, write a declarative `.rego` policy in `policies/agent_rbac.rego`.

```rego
# Example: Allow factory_ceo to use all tools
allow {
    input.agent == "factory_ceo"
}

# Example: Allow yaml_compiler to strictly write .yaml files
allow {
    input.agent == "yaml_compiler"
    input.tool == "write_file"
    endswith(input.payload.kwargs.file_path, ".yaml")
}
```
