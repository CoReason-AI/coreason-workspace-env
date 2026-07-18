# Reflexion & Self-Critique

> **Taxonomy Bucket**: `workflow/`
> **Scope**: Enabling autonomous self-improvement and failure recovery.

Purely reactive agents retry blindly when a task fails, often repeating the exact same error. To build self-improving agents, Builders must inject the Reflexion framework.

### The Reflexion Prompting Structure
Inject the following protocol for error handling:

1. **The Execution Trace**: "If your tool execution fails or the environment returns an error, you must STOP."
2. **The Critique Phase**: "Before attempting a new solution, output a `<Self_Critique>` block. Explicitly analyze the entire execution trace leading up to the failure. State precisely what assumption was incorrect."
3. **Adaptive Re-planning**: "Formulate a new `<Adaptive_Plan>` that explicitly avoids the isolated error before executing the next action."

By forcing the LLM to write out its failure analysis, you leverage "Test-Time Compute" to debug the logic rather than relying on token-probability guessing.
