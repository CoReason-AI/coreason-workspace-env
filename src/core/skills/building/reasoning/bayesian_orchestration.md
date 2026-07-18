# Bayesian Belief Updating (Orchestrators)

> **Taxonomy Bucket**: workflow/
> **Scope**: Tracking prior and posterior beliefs for uncertain routing.

### 1. Schema
For orchestrators routing tasks or managing uncertainty, explicitly track the probabilistic world model:
```json
{
  "bayesian_belief_state": {
    "latent_variables": [
      {
        "variable_name": "tool_x_reliability",
        "prior_probability": 0.5,
        "observed_evidence": "Tool failed on complex input",
        "posterior_probability": 0.2
      }
    ],
    "decision_taken": "Route to expert human instead of Tool X"
  }
}
```

### 2. Probability Derivation Instruction
The `prior_probability` and `posterior_probability` MUST NOT be arbitrarily guessed. You must enforce the following:
- **Mathematical Updates**: If possible, offload the Bayes theorem calculation ($P(A|B) = \frac{P(B|A)P(A)}{P(B)}$) to a deterministic python tool.
- **Historical Data**: Seed `prior_probability` with empirical historical success rates of the tools/agents (e.g., from telemetry databases).
28: - **If LLM-Calculated**: You MUST explicitly show your Bayes calculation in a scratchpad before generating the JSON payload.
29: 
---

### Refusal Predicate & Negative Constraints
- **When to Halt**: If routing decisions are purely deterministic (e.g., hardcoded if/else conditions) and involve zero uncertainty, halt and bypass the Bayesian calculation overhead.
- **Negative Constraints**: You are strictly forbidden from arbitrarily guessing the `prior_probability` and `posterior_probability` without a mathematical derivation or empirical telemetry data.
