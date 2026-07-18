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
```


### Integration Contract
- **Compute Constraints**: Stateless
- **Side-Effect Risk**: Read-Only


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
