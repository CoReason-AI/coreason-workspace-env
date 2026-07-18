# Workflow Building Standards

> **Taxonomy Bucket**: workflow/
> **Scope**: This skill is a construction guide for factory agents that **create** agentic workflows (cyclic graphs). It defines how to structure workflow topologies, handoffs, and routing. It does NOT contain validation checklists — those live in `validation/workflow_validation_standards.md`.

---

## 1. Hybrid MAS Topology

Avoid single-stage sequential pipelines for complex, multi-variable problems. Default to a Hybrid Multi-Agent System (HMAS) topology:

- **Supervisor Agent**: A central supervisory agent sets policies, goals, and strict sequencing
- **Decentralized Workers**: Dispatch specific tasks to scoped worker agents for exploratory execution and asynchronous discovery
- **Builder-Validator-Approver**: Every workflow MUST formally separate roles:
  - The agent that **drafts** the data (Builder) cannot be the same agent that **validates** it (Validator)
  - Neither can be the agent that **signs it off** (Approver)

## 2. Cyclic Routing & Feedback Loops

Unlike basic DAGs, advanced agentic workflows require cyclic loops for multi-hop reasoning and failure recovery:

- Workflows must explicitly define feedback loops (e.g., if the Validator rejects the Builder's draft, route back to the Builder with a specific `remediation_directives` schema)
- **Circuit Breakers**: Implement strict retry limits on all loops to prevent runaway token costs and infinite cycles
- Define maximum iteration counts for every feedback loop

## 3. Strict Pydantic Handoff Contracts

Agents do NOT "chat" with each other. They exchange structured data.

- **No Conversational Fluff**: Data passed between nodes must be strictly structured Pydantic schemas or JSON
- **Schema Depth & Width Limits**: Handoff schemas must be `≤ 3` levels deep with 5-8 parameters per level
- Every edge in the workflow graph must have a defined handoff schema

## 4. Context Window Discipline

Do not rely on massive context windows — they induce persona drift.

- **Working Memory Limits**: Each node receives only the exact data required for its specific atomic task — not the entire workflow history
- **Memory Promotion**: Workflows must define when data is held in active working memory vs. when it is promoted to long-term persistent storage (vector DB, graph DB, etc.)

## 5. Tool Node Encapsulation

Do not rely on every agent individually querying external APIs.

- **Standardized MCP Servers**: Use Tool Nodes powered by MCP servers to standardize tool execution and data retrieval
- **Colocation**: Place tool nodes between planner agents and worker agents to centralize caching and reduce API latency

## 6. Integration Contract

Every workflow specification MUST define an Integration Contract for framework-agnostic execution:

- **Topology Type**: Directed Cyclic Graph (DCG) with feedback loops, Sequential Pipeline, or Parallel Fan-Out/Join
- **State Persistence**: Ephemeral state or durable Write-Ahead Log (WAL) for mid-flight crash recovery
- **Concurrency Model**: Parallel or strict synchronous execution
- **Handoff Schema**: Reiterate the `≤ 3` level Pydantic schema rule and state exact schema boundaries

## 7. Provenance & Chain of Custody

Workflows that yield final authoritative outputs must establish a chain of custody:

- No node may inject factual data into the pipeline without attaching strict provenance metadata (`citation_ids`, `source_nodes`)
61: - The final node should run an integrity check verifying all claims trace back to a verified origin node
62: 
---

## 8. Refusal Predicate & Negative Constraints
- **When to Halt**: If instructed to validate an existing workflow against correctness, halt and refuse. This skill is strictly for *building* new workflows. Use `validation/workflow_validation_standards.md` for validation tasks.
- **Negative Constraints**: Workflows must never rely on massive context windows to solve multi-variable problems; you are strictly forbidden from designing single-stage monolithic pipelines for complex tasks.
