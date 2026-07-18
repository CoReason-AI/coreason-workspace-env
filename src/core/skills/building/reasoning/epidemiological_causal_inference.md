# Epidemiological Causal Inference

> **Taxonomy Bucket**: workflow/
> **Scope**: Evaluation of causal hypotheses using Bradford Hill Criteria.

Agents performing epidemiological analysis must evaluate against Bradford Hill criteria.
```json
{
  "causal_evaluation": {
    "hypothesis": "Exposure X causes Outcome Y",
    "hills_criteria": {
      "strength_of_association": "high|medium|low",
      "consistency": "high|medium|low",
      "specificity": "high|medium|low",
      "temporality_established": true,
      "biological_gradient": "observed|not_observed",
      "plausibility": "high|medium|low",
      "coherence": "high|medium|low",
      "experimental_evidence": "high|medium|low",
      "analogy": "high|medium|low"
    },
    "confounders_identified": ["string"],
    "mediators_identified": ["string"]
  }
}
```
