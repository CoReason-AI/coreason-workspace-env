# Multiple Choice Interrogation

> **Taxonomy Bucket**: workflow/
> **Scope**: How orchestrators clarify ambiguous intent and prompt the user.

When the Orchestrator identifies that the user's intent is underspecified and requires clarification, it must NOT ask open-ended questions. Humans prefer to select from curated options rather than writing extensive open-ended requirements.

### 1. Generate the 3 Best Options
When preparing to `INTERROGATE` the user, you must use your reasoning capabilities to deduce the **3 most logical architectural options** that resolve the ambiguity. 

CRITICAL: You are designing DeepAgent backend topologies (YAML manifests), NOT frontend user interfaces. Do not ask about Web, CLI, or Mobile apps. 
Your multiple-choice options MUST focus exclusively on resolving ambiguities in these 5 areas:
- **Topology (`type` / `dependencies`)**: Should this be a single worker agent, or a Supervisor delegating to multiple specialized subagents?
- **Tooling (`tools`)**: Which specific tools, APIs, or MCP servers are required to accomplish the task?
- **Knowledge (`skills`)**: Does the agent need specific domain guidelines, formatting rules, or SOPs injected into its context?
- **Persona (`system_prompt`)**: What specific tone, persona, or strict constraints must the agent adopt?
- **Data Contract (`input` / `output`)**: What is the expected structure of the input payload, and what precise output format should the agent produce (e.g., structured JSON, raw Markdown, a file artifact)?

Present these options clearly and concisely to the user, labeled A, B, and C. Briefly explain the trade-offs for each option.

### 2. Provide an "Other" Option
You must always append a final explicit option allowing the user to bypass your suggestions.
- **Option D**: "Other (please specify)"

### 3. Output Format
Format your interrogation response exactly as a multiple-choice list:
```markdown
[Clarifying Question Here]

A) [Option 1] - [Brief explanation]
B) [Option 2] - [Brief explanation]
C) [Option 3] - [Brief explanation]
D) Other (please specify)
```

### Refusal Predicate & Negative Constraints
- **When to Halt**: If a user's prompt is completely coherent, contextually saturated, and requires no further clarification, do not invent artificial multiple-choice questions. Proceed directly to delegation.
- **Negative Constraints**: You are strictly forbidden from asking open-ended questions (e.g., "What else do you want me to do?"). You must always synthesize ambiguity into 3 concrete options.
