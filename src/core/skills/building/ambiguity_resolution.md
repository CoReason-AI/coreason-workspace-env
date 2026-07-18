# Ambiguity Resolution & Poorly Defined Prompts

> **Taxonomy Bucket**: workflow/
> **Scope**: How orchestrators handle underspecified intent.

LLMs are prone to guessing user intent when provided with a poorly defined prompt. In a rigorous factory environment, this is unacceptable.

### 1. State Machine Interrogation (The Context Sink)
Orchestrators must act as a State Machine designed to reach "Context Saturation."
- If the incoming prompt is vague or lacks required schema fields, the Orchestrator MUST NOT attempt to guess the missing parameters.
- It must loop back to the user with targeted, clarifying questions.
- It only delegates to worker agents once the internal context state is 100% saturated.

### 2. Dialectical Clarification
When a user prompt is structurally ambiguous (e.g., it could mean Architectural Pattern A or Architectural Pattern B):
- The Orchestrator must generate a **Thesis** (Interpretation A) and an **Antithesis** (Interpretation B).
- It presents both options explicitly to the user, highlighting the tradeoffs, and forces the user to select the correct path before proceeding.
18: - Never silently assume the default interpretation.
19: 
---

### Refusal Predicate & Negative Constraints
- **When to Halt**: If a user prompt is so fundamentally broken that multiple opposing interpretations cannot even be formed, halt the resolution process and reject the input entirely as invalid.
- **Negative Constraints**: Never silently assume the default interpretation of an ambiguous prompt. You must force the user to make an explicit choice.
