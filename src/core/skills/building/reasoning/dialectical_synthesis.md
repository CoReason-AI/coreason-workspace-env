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
25: ```
26: 
---

### Refusal Predicate & Negative Constraints
- **When to Halt**: If a problem is purely mathematical, syntactical, or has a single universally accepted optimal solution, halt and bypass dialectical synthesis to avoid false equivalence.
- **Negative Constraints**: You are strictly forbidden from generating the synthesis node until both the thesis and a structurally sound antithesis have been explicitly generated and logged.
