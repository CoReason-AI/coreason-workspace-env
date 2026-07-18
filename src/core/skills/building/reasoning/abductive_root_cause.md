# Abductive Root-Cause Isolation

> **Taxonomy Bucket**: workflow/
> **Scope**: Finding the most plausible cause from observed symptoms.

### 1. Schema
For diagnostics and observability:
```json
{
  "abductive_inference": {
    "observed_symptoms": ["string"],
    "hypothesized_causes": [
      {
        "cause": "string",
        "explanatory_power_score": 0.0 - 1.0,
        "contradicted_by": ["string"]
      }
    ],
    "most_plausible_root_cause": "string"
  }
}
```

### 2. Explanatory Power Score Derivation
To prevent hallucinating an arbitrary `explanatory_power_score` (0.0 - 1.0), you MUST calculate it using the method defined in your system prompt:
- **Coverage Ratio (Rubric)**: Use a mathematical heuristic: `(Number of observed symptoms explained by hypothesis) / (Total number of observed symptoms)`.
- **Penalty Deductions**: Subtract 0.25 for every known symptom that explicitly contradicts the hypothesis.
- **Neuro-Symbolic Offloading**: Map the symptoms to variables and pass them to a Bayesian Network tool (e.g., `pgmpy`) to calculate the true conditional probability $P(Symptoms | Cause)$.
