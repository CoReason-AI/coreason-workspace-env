# Constraint Saturation Limits

> **Taxonomy Bucket**: workflow/
> **Scope**: Preventing "Over-steering" and the breakdown of LLM attention mechanisms.

When generating a system prompt, the `prompt_engineer` must explicitly limit the number of negative constraints and behavioral micro-adjustments in a single prompt.

### The Over-steering Problem
If a prompt is overloaded with stylistic or negative constraints (e.g., "Do not use word X", "Be funny but professional", "Use short sentences"), the LLM's attention mechanism allocates all processing power to juggling the constraints rather than generating natural, quality output. This causes **regression to the mean** (robotic, formulaic prose).

### Rule: Positive Steering First
- Limit negative constraints to an absolute maximum of 3 per prompt.
- Instead of telling an agent what NOT to do, define exactly what a successful output looks like.
- If more than 3 negative constraints are required to enforce safety, the task must be delegated to a downstream `output_sanitizer` or `agent_validator` rather than overburdening the generation agent's prompt.
