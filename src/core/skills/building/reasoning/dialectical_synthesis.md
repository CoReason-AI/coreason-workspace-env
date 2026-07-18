# Dialectical Synthesis

> **Taxonomy Bucket**: workflow/
> **Scope**: State geometry for Thesis -> Antithesis -> Synthesis critique loops.

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
