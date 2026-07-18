# Tree of Thoughts (ToT) Exploration

> **Taxonomy Bucket**: `workflow/`
> **Scope**: Forcing System 2 deliberation via branching, pruning, and backtracking.

When an agent is assigned a high-stakes analytical, creative, or architectural task, do not allow it to generate a single answer linearly. Instruct it to use the Tree of Thoughts (ToT) framework.



### Integration Contract
- **Compute Constraints**: Stateless
- **Side-Effect Risk**: Read-Only

### The ToT Prompting Structure
Inject the following explicit rules into the agent's `<Workflow>`:

1. **Thought Decomposition**: "Do not attempt to solve the problem immediately. First, explicitly decompose the problem into 3 distinct, divergent hypotheses or strategic paths."
2. **Heuristic Evaluation**: "For each path, explicitly evaluate its viability. State the pros, cons, and potential failure modes."
3. **Pruning & Backtracking**: "Select the single most promising path and expand it. If you encounter a logical dead-end during expansion, explicitly output `<Backtrack>` and return to the next best evaluated path."

This forces the LLM's attention mechanism to simulate human planning and prevents premature commitment to a hallucinated strategy.


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
