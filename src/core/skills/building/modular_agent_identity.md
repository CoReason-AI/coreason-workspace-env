# Modular Agent Identity

> **Taxonomy Bucket**: persona/
> **Scope**: Preventing system prompt bloat by modularizing personality and rules.

Do not cram every behavioral rule, safety guideline, and tone instruction into a single massive `system_prompt` block. 

### Modular Injection
When compiling agent definitions, separate concerns into modular markdown files that are JIT-loaded:

1. **`IDENTITY.md`**: Core safety, privacy, and absolute behavioral constraints (e.g., "Never expose API keys").
2. **`SOUL.md`**: Tone, persona, and interaction style (e.g., "Speak concisely, do not apologize, avoid moralizing").
3. **`AGENTS.md`**: Standard operating procedures, repository rules, and architectural guidelines.

**Rule for Builders**:
16: The final `system_prompt` in the YAML should only contain the immediate task `<Workflow>` and `<OutputFormat>`. The `<Constraints>` and `<Profile>` should be referenced via the `skill_registry` from these modular files.
17: 
---

### Refusal Predicate & Negative Constraints
- **When to Halt**: If an agent's required behavior is so highly specific and tightly coupled to a single task that it cannot be cleanly modularized without losing nuance, you may bypass modular injection and write a monolithic prompt.
- **Negative Constraints**: Do not cram every generic behavioral rule, safety guideline, and tone instruction into a single massive `system_prompt` block.
