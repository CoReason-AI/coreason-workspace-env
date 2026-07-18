# Dynamic Context Pipelines

> **Taxonomy Bucket**: workflow/
> **Scope**: Defining the holistic ecosystem of an agent's context beyond just the static prompt.

Context Engineering transcends Prompt Engineering. An agent's behavior is dictated by the entire informational payload surrounding its inference. When constructing an Orchestrator or a full application, you must define a **Dynamic Context Pipeline**.

### The 4 Pillars of Context Engineering

When generating `agent.yaml` or application code, explicitly define rules for these four pillars:

1. **Prompt & Identity**: The static system instructions, defined via XML tagging (`<Role>`, `<Goals>`).
2. **Tool Surface Area**: Do not inject all 50 MCP tools into every agent. Define routing layers that dynamically load only the tools necessary for the current sub-state. A focused capability surface drastically reduces tool-use hallucinations.
3. **Memory & State (History)**: Explicitly dictate how conversation history is truncated. For long-running workflows, mandate the use of `context_compaction_protocol.md` to summarize past events into a dense `<State_Summary>` rather than appending raw turn-by-turn history.
4. **Episodic Retrieval (RAG/Resources)**: Define precisely *when* and *how* external facts (e.g., from an MCP Resource or vector store) are injected into the context window. Ensure injected facts contain strict provenance metadata.

### System Design Constraint
18: *"Do not assume the LLM will magically sort out irrelevant information. You must engineer the pipeline so that at any given step $T$, the context window contains the minimal, strictly relevant payload required to transition to step $T+1$."*
19: 
---

### Refusal Predicate & Negative Constraints
- **When to Halt**: If requested to build an agent that injects all available tools indiscriminately without a routing layer, halt and refuse, citing this dynamic context constraint.
- **Negative Constraints**: Never allow raw turn-by-turn history to append indefinitely. You must enforce memory boundaries.
