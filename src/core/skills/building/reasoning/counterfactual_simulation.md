# Counterfactual Simulation (Do-Calculus)

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
