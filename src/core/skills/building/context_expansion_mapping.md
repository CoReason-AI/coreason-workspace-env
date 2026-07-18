# Context Expansion Mapping

> **Taxonomy Bucket**: `workflow/`
> **Scope**: Preventing isolated reasoning by forcing lateral ontological lookups (e.g., "Class Effects").
> **Origin**: Inspired by `context_expansion_pharmacological_class_tool.md` from the Fractal Study.

When an agent is investigating a highly specific anomaly (e.g., a bug in a specific file, or an adverse event for a specific drug), it is prone to tunnel vision. You must build a mechanism that forces the agent to look at the lateral context to see if the anomaly is a systemic "class effect."



### Integration Contract
- **Compute Constraints**: Stateless
- **Side-Effect Risk**: Read-Only

### The Expansion Prompting Structure
Inject the following rigid framework into the agent's `<Workflow>`:

1. **Expansion Trigger**: "When investigating an anomaly in Entity X, you are forbidden from drawing a conclusion based solely on Entity X."
2. **Ontological Traversal**: "You must execute a lateral expansion step. Identify the taxonomy or class of Entity X (e.g., 'HMG CoA reductase inhibitors', or 'Frontend Auth Middleware')."
3. **Sibling Lookup**: "Fetch data on 3 sibling entities that share the same class."
4. **Synthesis**: "Compare the anomaly in Entity X against its siblings. State explicitly whether this is an isolated incident or a systemic class effect before proceeding."


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
