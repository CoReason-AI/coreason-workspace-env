# Bayesian Belief Updating (Orchestrators)

> **Taxonomy Bucket**: workflow/
> **Scope**: Tracking prior and posterior beliefs for uncertain routing.



### Integration Contract
- **Compute Constraints**: Stateless
- **Side-Effect Risk**: Read-Only

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
- **If LLM-Calculated**: You MUST explicitly show your Bayes calculation in a scratchpad before generating the JSON payload.


### Refusal Predicate & Negative Constraints
- **When to Halt**: If the required context is missing, immediately halt execution and return a failure state. Do not attempt to guess or hallucinate parameters.
- **Negative Constraints**: You are strictly forbidden from executing operations outside this defined scope.
