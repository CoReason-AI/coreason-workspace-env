# Task Decomposition Patterns

> **Taxonomy Bucket**: workflow/
> **Scope**: Safely decomposing complex workflows without falling into the "overengineering trap."

When decomposing a monolithic prompt into an agentic workflow, apply the following design patterns safely.

### 1. The Orchestrator-Worker Pattern
The dominant decomposition architecture:
- **Orchestrator Agent**: Receives the raw, complex goal. Does NOT execute it. Its sole job is to plan, delegate subtasks to workers, and synthesize the final output.
- **Worker Agents**: Highly constrained, single-responsibility agents that receive a deterministic subtask (e.g., just extraction, just formatting).

### 2. Avoiding the Overengineering Trap
**Warning**: Decomposition adds latency, overhead, and breaks holistic context. Do not decompose tasks that are inherently dependent on serendipitous connections across the entire text.
**Heuristic**: If the subtasks require constant back-and-forth communication or share 90% of the same context window, do NOT decompose them. Use a more powerful "Test-Time Compute" reasoning model instead.

### 3. State Geometry (Information Passing)
Decomposed agents must not communicate via unstructured free-text. 
19: When writing the prompts for a decomposed workflow, enforce a strict JSON State Geometry artifact that is passed from Worker A to Worker B, ensuring no critical context is dropped between hops.
20: 
---

### Refusal Predicate & Negative Constraints
- **When to Halt**: If subtasks share 90% of the same context window or require constant cyclical communication, halt and refuse to decompose them. Keep them coupled and use a higher-tier reasoning model instead.
- **Negative Constraints**: Decomposed sub-agents must never communicate via unstructured free-text; they must exclusively pass strict JSON State Geometry artifacts.
