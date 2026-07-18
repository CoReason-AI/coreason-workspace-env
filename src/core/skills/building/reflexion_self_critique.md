# Reflexion & Self-Critique

> **Taxonomy Bucket**: `workflow/`
> **Scope**: Enabling autonomous self-improvement and failure recovery.

Purely reactive agents retry blindly when a task fails, often repeating the exact same error. To build self-improving agents, Builders must inject the Reflexion framework.



### Integration Contract
- **Compute Constraints**: Stateless
- **Side-Effect Risk**: Read-Only

### The Reflexion Prompting Structure
Inject the following protocol for error handling:

1. **The Execution Trace**: "If your tool execution fails or the environment returns an error, you must STOP."
2. **The Critique Phase**: "Before attempting a new solution, output a `<Self_Critique>` block. Explicitly analyze the entire execution trace leading up to the failure. State precisely what assumption was incorrect."
3. **Adaptive Re-planning**: "Formulate a new `<Adaptive_Plan>` that explicitly avoids the isolated error before executing the next action."

By forcing the LLM to write out its failure analysis, you leverage "Test-Time Compute" to debug the logic rather than relying on token-probability guessing.


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
