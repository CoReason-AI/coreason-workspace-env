# Modular Agent Identity

> **Taxonomy Bucket**: persona/
> **Scope**: Preventing system prompt bloat by modularizing personality and rules.

Do not cram every behavioral rule, safety guideline, and tone instruction into a single massive `system_prompt` block. 



### Integration Contract
- **Compute Constraints**: Stateless
- **Side-Effect Risk**: Read-Only

### Modular Injection
When compiling agent definitions, separate concerns into modular markdown files that are JIT-loaded:

1. **`IDENTITY.md`**: Core safety, privacy, and absolute behavioral constraints (e.g., "Never expose API keys").
2. **`SOUL.md`**: Tone, persona, and interaction style (e.g., "Speak concisely, do not apologize, avoid moralizing").
3. **`AGENTS.md`**: Standard operating procedures, repository rules, and architectural guidelines.

**Rule for Builders**:
The final `system_prompt` in the YAML should only contain the immediate task `<Workflow>` and `<OutputFormat>`. The `<Constraints>` and `<Profile>` should be referenced via the `skill_registry` from these modular files.


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
