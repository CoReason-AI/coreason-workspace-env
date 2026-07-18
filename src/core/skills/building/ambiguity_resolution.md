# Ambiguity Resolution & Poorly Defined Prompts

> **Taxonomy Bucket**: workflow/
> **Scope**: How orchestrators handle underspecified intent.

LLMs are prone to guessing user intent when provided with a poorly defined prompt. In a rigorous factory environment, this is unacceptable.



### Integration Contract
- **Compute Constraints**: Stateless
- **Side-Effect Risk**: Read-Only

### 1. State Machine Interrogation (The Context Sink)
Orchestrators must act as a State Machine designed to reach "Context Saturation."
- If the incoming prompt is vague or lacks required schema fields, the Orchestrator MUST NOT attempt to guess the missing parameters.
- It must loop back to the user with targeted, clarifying questions.
- It only delegates to worker agents once the internal context state is 100% saturated.

### 2. Dialectical Clarification
When a user prompt is structurally ambiguous (e.g., it could mean Architectural Pattern A or Architectural Pattern B):
- The Orchestrator must generate a **Thesis** (Interpretation A) and an **Antithesis** (Interpretation B).
- It presents both options explicitly to the user, highlighting the tradeoffs, and forces the user to select the correct path before proceeding.
- Never silently assume the default interpretation.


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
