# Glass Box Traceability

> **Taxonomy Bucket**: workflow/
> **Scope**: Explicit assumption boundaries for FDA/GxP compliance.



### Integration Contract
- **Compute Constraints**: Stateless
- **Side-Effect Risk**: Read-Only

### 1. Schema
For FDA/GxP compliance, agents MUST output this block before executing any action.
```json
{
  "glass_box_traceability": {
    "action_intent": "string",
    "assumed_facts": [
      {
        "fact": "string",
        "source": "string",
        "confidence": 0.0 - 1.0
      }
    ],
    "regulatory_constraints_respected": ["string"],
    "domain_boundaries": {
      "what_i_know": ["string"],
      "what_i_do_not_know": ["string"]
    }
  }
}
```

### 2. Confidence Derivation Instruction
To prevent hallucinated `confidence` scores (0.0 - 1.0), you MUST use the following verifiable rubric to score your assumptions:
- **1.0 (Absolute)**: Fact is retrieved directly from a trusted external system/database.
- **0.75 (High)**: Fact is synthesized from multiple congruent contexts.
- **0.5 (Moderate)**: Fact is inferred, but contains some ambiguity or reliance on parametric memory.
- **0.25 (Low)**: Fact is a weakly supported assumption.
You MUST explicitly justify the selected tier in your `deliberation_trace` prior to outputting the score.


### Refusal Predicate & Negative Constraints
- **When to Halt**: If the required context is missing, immediately halt execution and return a failure state. Do not attempt to guess or hallucinate parameters.
- **Negative Constraints**: You are strictly forbidden from executing operations outside this defined scope.
