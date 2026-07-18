# Multiple Choice Interrogation

> **Taxonomy Bucket**: workflow/
> **Scope**: How orchestrators clarify ambiguous intent and prompt the user.

When the Orchestrator identifies that the user's intent is underspecified and requires clarification, it must NOT ask open-ended questions. Humans prefer to select from curated options rather than writing extensive open-ended requirements.



### Integration Contract
- **Compute Constraints**: Stateless
- **Side-Effect Risk**: Read-Only

### 1. Generate the 3 Best Options
When preparing to `INTERROGATE` the user, you must use your reasoning capabilities to deduce the **3 most logical architectural or design options** that would resolve the ambiguity. 
- Present these options clearly and concisely to the user, labeled A, B, and C.
- Briefly explain the reasoning or trade-offs for each option.

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
