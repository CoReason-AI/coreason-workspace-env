# Analogical & Structural Mapping

> **Taxonomy Bucket**: workflow/
> **Scope**: Structural templates and schemas for Analogical Prompting and Transfer.



### Integration Contract
- **Compute Constraints**: Stateless
- **Side-Effect Risk**: Read-Only

### 1. Analogical Prompting Template
Inject this into the system prompt of agents performing zero-shot reasoning:
```markdown
**Analogical Scaffolding Constraint**: Before attempting to solve the target problem, you MUST generate 3 diverse, relevant problems from different domains that share the same structural properties. 
1. Explain the solution to each generated problem.
2. Construct an Explicit Structural Mapping (see schema) linking the source domain to the target domain.
3. Only then, synthesize the final answer.
```

### 2. Explicit Structural Mapping Schema
Agents must output this JSON artifact before transferring knowledge:
```json
{
  "mapping_artifact": {
    "source_domain": "string",
    "target_domain": "string",
    "entities": [
      {
        "source_entity": "string",
        "target_entity": "string",
        "role_in_system": "string"
      }
    ],
    "relations": [
      {
        "source_relation": "A causes B",
        "target_relation": "X causes Y",
        "structural_similarity_score": 0.0 - 1.0
      }
    ]
  }
}
```

### 3. Score Derivation Instruction
To prevent hallucinating an arbitrary `structural_similarity_score` (0.0 - 1.0), you MUST calculate it using the method defined in your system prompt:
- **Heuristic Rubric**: Calculate the score based on exact matches of nodes and edges (e.g., `(Matching Nodes + Matching Edges) / Total Entities in Target`).
- **External Causal Engine**: Pass the mapped graph to a graph-matching tool (e.g., NetworkX isomorphism check) to calculate the score.
- **Test-Time Compute**: If you are a reasoning model, explicitly list similarities and differences in a scratchpad before estimating the normalized score.


### Refusal Predicate & Negative Constraints
- **When to Halt**: If the required context is missing, immediately halt execution and return a failure state. Do not attempt to guess or hallucinate parameters.
- **Negative Constraints**: You are strictly forbidden from executing operations outside this defined scope.
