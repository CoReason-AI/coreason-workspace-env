# Reflexion & Self-Critique

> **Taxonomy Bucket**: workflow/
> **Scope**: Enabling autonomous self-improvement and failure recovery.

Purely reactive agents retry blindly when a task fails, often repeating the exact same error. To build self-improving agents, Builders must inject the Reflexion framework.

### The Reflexion Prompting Structure
Inject the following protocol for error handling:

1. **The Execution Trace**: "If your tool execution fails or the environment returns an error, you must STOP."
2. **The Critique Phase**: "Before attempting a new solution, output a `<Self_Critique>` block. Explicitly analyze the entire execution trace leading up to the failure. State precisely what assumption was incorrect."
3. **Adaptive Re-planning**: "Formulate a new `<Adaptive_Plan>` that explicitly avoids the isolated error before executing the next action."

15: By forcing the LLM to write out its failure analysis, you leverage "Test-Time Compute" to debug the logic rather than relying on token-probability guessing.
16: 
---

### Refusal Predicate & Negative Constraints
- **When to Halt**: If a failure is definitively identified as a fatal infrastructural outage (e.g., 503 Server Unavailable) rather than a logic error, halt execution entirely rather than spinning in a futile critique loop.
- **Negative Constraints**: Never blindly retry the exact same action after a failure without first outputting the explicit `<Self_Critique>` block.
