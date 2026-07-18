# Agentic Design Patterns Catalog

> **Taxonomy Bucket**: workflow/
> **Scope**: A comprehensive architectural guide detailing the 12 standard workflow patterns for multi-agent systems.

### 🚨 Critical Architecture Constraint: DeepAgents 0.6.0+ & LangChain v1
Every pattern in this catalog **MUST** be implemented natively using `deepagents >= 0.6.0` and the modern **LangChain v1** API.
- **DO NOT** use legacy `AgentExecutor` or `initialize_agent` when building these patterns.
- **DO NOT** use deprecated `langchain-community` abstractions.
- All patterns (Routing, Plan-and-Execute, Orchestrator) must be built using LangGraph `StateGraph`, `create_agent`, and native tool calling, following the strict deepagents v0.6.0 API contract.

When deciding how to route tasks in `workflow_building_standards.md`, use these foundational topologies:

### The 4 Foundational Patterns (Ng)
1. **Reflection**: The agent generates an output, then critiques its own output to improve it.
2. **Tool Use**: The agent uses external tools (via MCP) to gather information or take action.
3. **Planning (Plan-and-Execute)**: The agent breaks down a complex goal into a sequence of smaller tasks before executing them.
4. **Multi-Agent Collaboration**: Multiple agents with distinct personas work together to solve a problem.

### The 5 Workflow Patterns (Anthropic)
5. **Routing**: A classifier agent routes the input to the most appropriate specialized sub-agent.
6. **Parallelization**: Tasks that do not depend on each other are executed simultaneously by multiple workers, then aggregated.
7. **Evaluator-Optimizer Loop**: One agent generates a solution; a second, distinct agent acts as a strict evaluator, looping until a threshold is met.
8. **Orchestrator-Workers**: A central supervisor plans and delegates subtasks to constrained workers (this is the dominant pattern in CoReason).
9. **Autonomous Agent**: An agent with an open-ended loop that uses tools and memory to iteratively solve a problem until it decides it is finished.

### Emergent Patterns (2025-2026)
10. **Metaprompting**: Using a reasoning model to write the production prompt for another model.
11. **Chain-of-Symbol (CoS)**: Using spatial tokens (`↑`, `↓`, `[x]`) instead of natural language for state-machine tracking.
12. **Consortium Governance**: A heterogeneous group of models generates candidate paths, and a distinct Governance Agent synthesizes the final auditable decision.
