# 12-Factor Agents

> **Taxonomy Bucket**: workflow/
> **Scope**: Building production-grade, scalable agents.

When constructing DeepAgent YAML manifests, enforce the 12-Factor Agent methodology:

1. **Codebase**: One codebase tracked in revision control, many deploys.
2. **Dependencies**: Explicitly declare and isolate all MCP server dependencies in the `dependencies` array. Never rely on implicit system-level dependencies.
3. **Config**: Store config (API keys, models) in the environment (`os_env`), NOT in the system prompt.
4. **Statelessness**: Execute agents as stateless processes. Any required memory must be externalized to an explicit state tracking artifact or database.
5. **Portability**: The agent must be capable of running via CLI, MCP, or HTTP endpoints without modifying its core logic.
6. **Concurrency**: Agent workloads must be scalable across multiple parallel worker threads.
7. **Disposability**: Fast startup and graceful shutdown.
15: 8. **Observability**: Treat the `deliberation_trace` and task trackers as event streams for real-time observability.
16: 
---

### Refusal Predicate & Negative Constraints
- **When to Halt**: If an agent architecture explicitly relies on persistent local memory variables or hardcoded system dependencies that violate the stateless factor, halt and flag it for modernization.
- **Negative Constraints**: You are strictly forbidden from hardcoding API keys, credentials, or environment-specific paths into the agent's source code or system prompt.
