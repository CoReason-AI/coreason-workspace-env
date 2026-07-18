# Dialectical Synthesis

> **Taxonomy Bucket**: workflow/
> **Scope**: State geometry for Thesis -> Antithesis -> Synthesis critique loops.



### Integration Contract
- **Compute Constraints**: Stateless
- **Side-Effect Risk**: Read-Only

### State Geometry
For creative or ambiguous tasks, the agent's internal state must track the dialectic:
```json
{
  "dialectical_state": {
    "thesis": {
      "proposed_solution": "string",
      "supporting_evidence": ["string"]
    },
    "antithesis": {
      "counter_argument": "string",
      "structural_flaws": ["string"]
    },
    "synthesis": {
      "reconciled_solution": "string",
      "tradeoffs_accepted": ["string"]
    }
  }
}
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
