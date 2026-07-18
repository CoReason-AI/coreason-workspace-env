# Structured Meta-Prompting (LangGPT Pattern)

> **Taxonomy Bucket**: workflow/
> **Scope**: Framework for writing rigorous, code-like system prompts.

When writing a system prompt, do not use unstructured natural language paragraphs. All system prompts MUST be structured using rigid pseudo-code tags to reduce hallucination and ensure deterministic behavior.

### The Template
Enforce the following structure for all agent prompts:

```markdown
<Role>
You are an expert [Role Name] agent operating within the CoReason environment.
</Role>

<Profile>
- **Identity**: [Brief description]
- **Core Function**: [Primary objective]
</Profile>

<Goals>
1. [Goal 1]
2. [Goal 2]
</Goals>

<Constraints>
- NEVER [Constraint 1]
- YOU MUST [Constraint 2]
</Constraints>

<Workflow>
1. Evaluate: [Step 1]
2. Interrogate: [Step 2]
3. Delegate: [Step 3]
</Workflow>

<OutputFormat>
Strictly adhere to the following JSON schema:
[Insert Schema]
</OutputFormat>
```

### The Metaprompting Strategy (2026)
When an orchestrator must define the system prompt for a new deterministic sub-agent, do not write the prompt directly. Use the **Metaprompting Strategy**:
- Instruct a frontier reasoning model (e.g., DeepSeek-R1 or GPT-5) to generate the XML tags.
- The reasoning model acts as the "compiler" translating the goals into the rigid XML structure optimized for a faster production model (e.g., GPT-4o-mini).
