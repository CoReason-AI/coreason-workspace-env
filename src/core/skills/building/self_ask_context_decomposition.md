# Self-Ask Context Decomposition

> **Taxonomy Bucket**: `workflow/`
> **Scope**: Explicitly building a contextual foundation before generating solutions.

Often, an agent attempts to answer a complex or ambiguous user prompt immediately, leading to hallucinations because it lacks the necessary environmental context. You must instruct the agent to build its own context first.

### The Self-Ask Framework
Inject the following rigid constraints into the agent's `<Workflow>`:

1. **Context Block Declaration**: "Before executing the primary objective, you MUST evaluate the prompt and declare a `<Context_Requirements>` block."
2. **Sub-Question Generation**: "In the `<Context_Requirements>` block, list the exact sub-questions, missing variables, or historical facts that must be resolved to safely execute the task."
3. **Mandatory Resolution**: "You are forbidden from generating the final solution until every question in the `<Context_Requirements>` block has been answered via tool execution or explicitly waived by the user."

### Why This Works
This forces the LLM to spend "test-time compute" explicitly recognizing its own epistemic gaps. By generating the sub-questions, it effectively prompts its future self to seek out the correct context via MCP tools before attempting a zero-shot hallucination.
