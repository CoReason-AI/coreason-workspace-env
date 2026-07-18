# Cognitive Skill Taxonomy

> **Taxonomy Bucket**: workflow/
> **Scope**: Standardizing how the factory categorizes agent skills.

When creating or declaring skills in a `skill_registry`, builders MUST categorize them into one of three strict taxonomy buckets. This mirrors the `awesome-language-agents` architecture.

### The Three Taxonomy Buckets
1. **`persona/` (Role-Based Stances)**: Professional identities that define epistemic boundaries. 
   *Example*: `personas/expert_architect`, `personas/fda_regulator`.
2. **`tool/` (Technology Execution)**: Specific syntax or platform rules. 
   *Example*: `tools/pgmpy_syntax`, `tools/react_router_v6`.
3. **`workflow/` (Process-Driven Loops)**: Methodologies for executing cognitive loops. 
   *Example*: `workflows/test_driven_development`, `workflows/abductive_triage`.

**Rule for Builders**:
Never mix these buckets in a single skill file. A skill that teaches an agent *how to use a tool* should not also define its *persona*. Keep skills orthogonal.

---

### Refusal Predicate & Negative Constraints
- **When to Halt**: If instructed to categorize a skill outside of the three defined buckets (`persona/`, `tool/`, `workflow/`), halt and refuse.
- **Negative Constraints**: Never mix taxonomy buckets in a single skill file.
