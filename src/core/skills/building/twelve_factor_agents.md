# 12-Factor Agents

> **Scope**: Building production-grade, scalable agents.

When constructing DeepAgent YAML manifests, enforce the 12-Factor Agent methodology:

1. **Codebase**: One codebase tracked in revision control, many deploys.
2. **Dependencies**: Explicitly declare and isolate all MCP server dependencies in the `dependencies` array. Never rely on implicit system-level dependencies.
3. **Config**: Store config (API keys, models) in the environment (`os_env`), NOT in the system prompt.
4. **Statelessness**: Execute agents as stateless processes. Any required memory must be externalized to an explicit state tracking artifact or database.
5. **Portability**: The agent must be capable of running via CLI, MCP, or HTTP endpoints without modifying its core logic.
6. **Concurrency**: Agent workloads must be scalable across multiple parallel worker threads.
7. **Disposability**: Fast startup and graceful shutdown.
8. **Observability**: Treat the `deliberation_trace` and task trackers as event streams for real-time observability.
