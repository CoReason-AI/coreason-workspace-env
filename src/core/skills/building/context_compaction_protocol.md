# Context Compaction Protocol

> **Taxonomy Bucket**: `workflow/`
> **Scope**: Preventing reasoning degradation and context window exhaustion.
> **Origin**: Inspired by `context_compaction_protocol_tool.md` from the Fractal Study.

When building an Orchestrator or a Data Processing agent that must ingest massive payloads (e.g., 200-page clinical study reports, raw server logs), you must protect the agent's context window. LLMs suffer from the "lost in the middle" phenomenon if transient memory is not actively managed.

### The Compaction Prompting Structure
Inject the following explicit rules into the agent's `<Workflow>`:

1. **Transient Memory Limit**: "Do not attempt to hold the entire raw document in your working memory while reasoning."
2. **Periodic Serialization**: "After reading a chunk of data, you must output a `<Compacted_State>` block. This block must aggressively strip all boilerplate, conversational filler, and non-essential narrative."
3. **Data Loss Prevention**: "While stripping narrative, you MUST perfectly preserve exact numerical values, formulas, and schema keys related to the objective. Convert the verbose text into highly dense Key-Value pairs."
4. **State Passing**: "Pass only the `<Compacted_State>` to the next reasoning node, discarding the raw payload."
