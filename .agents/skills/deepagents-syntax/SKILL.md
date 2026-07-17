---
name: DeepAgents Syntax and Guidelines
description: Teaches how to construct and use deep agents utilizing the `create_deep_agent` API from the `deepagents` ecosystem (v0.6.0+). Triggers when the user asks to build or configure a deepagent, or mentions `deepagents`.
---

# DeepAgents Syntax (`>= 0.6.0`)

When generating Python code to build Deep Agents, you MUST adhere to the following constraints based on the `deepagents` SDK.

## Core Principles
1. **LangChain v1 Architecture**: `deepagents` strictly targets the modern LangChain v1 ecosystem.
2. **Factory Method**: Always use `create_deep_agent` from `deepagents.graph` to build agents. NEVER use the deprecated `langgraph.prebuilt.create_react_agent`.
3. **No Legacy Contracts**: We do not support legacy API contracts (e.g., deprecated `ls_info`, `grep_raw`, or `ASYNC_GREP_TIMEOUT`).
4. **State Schema**: Custom agent state schemas MUST inherit from `deepagents.graph.DeepAgentState` (which is a `TypedDict`), not Pydantic BaseModels or dataclasses.

## `create_deep_agent` Signature and Usage

```python
from deepagents.graph import create_deep_agent, DeepAgentState, SystemPromptConfig
from deepagents.backends import StateBackend
from langchain_anthropic import ChatAnthropic

# 1. Model must be explicitly instantiated. DO NOT use model=None.
model = ChatAnthropic(model_name="claude-sonnet-4-6")

# 2. State schemas must inherit from DeepAgentState (TypedDict)
class MyCustomState(DeepAgentState):
    user_context: str
    processed_items: int

# 3. Create the agent
agent = create_deep_agent(
    model=model,
    tools=[custom_tool1, custom_tool2], # Custom tools (additive to built-ins)
    system_prompt=SystemPromptConfig(
        prefix="You are an expert financial assistant.",
        # 'base' can be overridden, or omitted to keep default
        suffix="Always cite your sources."
    ),
    state_schema=MyCustomState,
    backend=StateBackend(), # Base backend; use SandboxBackendProtocol for shell execution
    permissions=[], # List of FilesystemPermission rules ('allow', 'deny', 'interrupt')
    interrupt_on={"custom_tool1": True}, # Human-in-the-loop triggers
    subagents=[], # List of SubAgent, CompiledSubAgent, or AsyncSubAgent
    skills=["/skills/financial_analysis"], # Posix paths relative to backend root
    memory=["/memory/AGENTS.md"] # Memory files to load at startup
)
```

## Key Parameter Definitions

- **`model`**: Must be explicitly instantiated (e.g. `ChatAnthropic(model_name="...")`). Relying on the default `model=None` is deprecated and will fail in `1.0.0`.
- **`system_prompt`**: Can be a string, a `SystemMessage`, or a `SystemPromptConfig` dict with `prefix`, `base`, and `suffix` keys. `prefix` goes before the built-in instructions, `suffix` goes after.
- **`subagents`**: An agent can delegate tasks via the `task` tool to these subagents:
  - `SubAgent`: Declarative spec (dict with `name`, `description`, `system_prompt`).
  - `CompiledSubAgent`: A pre-built runnable.
  - `AsyncSubAgent`: Remote subagent (requires `graph_id`). Runs as a background task.
- **`permissions`**: Rules enforcing file access (`"allow"`, `"deny"`, `"interrupt"`). Subagents inherit rules unless they define their own.
- **`interrupt_on`**: Dict mapping tool names to boolean/config for human-in-the-loop pauses.
- **`state_schema`**: Must be a `TypedDict` subclassing `DeepAgentState`. Forwarded to declarative `SubAgent`s but NOT to `CompiledSubAgent`s (which must be compiled with compatible schemas beforehand).

## Common Anti-Patterns (AVOID)
- ❌ **Anti-Pattern**: Using `model=None` as a shortcut.
- ❌ **Anti-Pattern**: Using `langgraph.prebuilt.create_react_agent`.
- ❌ **Anti-Pattern**: Defining `state_schema` as a Pydantic `BaseModel`. Must be `TypedDict` + `DeepAgentState`.
- ❌ **Anti-Pattern**: Importing legacy community packages (`langchain-community` is deprecated).
- ❌ **Anti-Pattern**: Modifying `system_prompt` by wrapping it in complex template strings instead of using `SystemPromptConfig`.
