# Counterfactual Simulation (Do-Calculus)

> **Taxonomy Bucket**: workflow/
> **Scope**: Simulating do-interventions via causal engines like dowhy.

When proposing interventions, the agent must output a causal graph definition.
```json
{
  "causal_graph": {
    "nodes": ["Treatment", "Outcome", "Confounder1"],
    "edges": [
      {"from": "Treatment", "to": "Outcome"},
      {"from": "Confounder1", "to": "Treatment"},
      {"from": "Confounder1", "to": "Outcome"}
    ],
    "proposed_intervention": {
      "action": "do(Treatment = 1)",
      "estimand_target": "Outcome"
    }
  }
}
22: ```
23: 
---

### Refusal Predicate & Negative Constraints
- **When to Halt**: If an intervention is purely superficial or cosmetic (e.g., changing a UI color) with no systemic downstream effects, halt and bypass the causal graph generation.
- **Negative Constraints**: You are strictly forbidden from proposing interventions in complex systems without first formally mapping known confounders in the `causal_graph` schema.
