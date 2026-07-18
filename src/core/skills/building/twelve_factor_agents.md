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
8. **Observability**: Treat the `deliberation_trace` and task trackers as event streams for real-time observability.


### Integration Contract
- **Compute Constraints**: Stateless
- **Side-Effect Risk**: Read-Only


### Output Schema
```json
{
  "action_result": {
    "status": "success",
    "details": "string"
  }
}
```


### Refusal Predicate & Negative Constraints
- **When to Halt**: If the required context is missing, immediately halt execution and return a failure state. Do not attempt to guess or hallucinate parameters.
- **Negative Constraints**: You are strictly forbidden from executing operations outside this defined scope.
