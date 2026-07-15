# Writing Validation Rules

The CoReason Workspace Environment fundamentally rejects stochastic self-correction (the "Generator-Critic" pattern). Instead, the platform relies on the **Maker-Checker-Approver** pipeline, where the Checker is a purely deterministic LangGraph node executing rigorous validation rules.

When authoring validation rules, you are writing the deterministic software logic that physically prevents hallucinated or malformed data from progressing through the graph.

## Location and Structure

Validation rules are stored as Skills within the Checker's dedicated library: `src/core/skills/validation/`.

A validation skill consists of a `SKILL.md` (defining the pass/fail checklist) and a Python script containing the deterministic evaluation logic.

## Types of Validation Rules

You must implement one or more of the following deterministic boundaries:

### 1. Pydantic Boundary Validation
The most common validation rule enforces strict adherence to a `coreason-manifest` schema. The validation script must load the generated JSON artifact and execute `Model.model_validate(json_data)`. If a `ValidationError` is raised, the script automatically generates an error payload detailing the exact missing or invalid fields, routing the state machine back to the Maker.

### 2. Abstract Syntax Tree (AST) Parsing
If the Maker generated Python code or an expression, the validation rule must parse the code using the native `ast` module. 
- Example: Ensure the code does not contain `eval()` or `exec()`.
- Example: Ensure all network requests route through the authorized `httpx` client rather than a raw socket.

### 3. Isolated Sandbox Execution
For complex outputs, the validation rule may compile and execute the generated artifact within an isolated container or an ephemeral WebAssembly (Wasm) sandbox, validating its standard output against the expected mathematical result.

## The Rule Writing Mandate

When writing a validation rule, follow these directives:
- **No LLM Calls**: You are strictly forbidden from utilizing a language model to "grade" or "evaluate" the artifact. If the validation cannot be represented mathematically or programmatically, it must be escalated to the Human-in-the-Loop Approver node.
- **Actionable Remediation**: If a validation fails, the script must return a deterministic `GuardrailViolationEvent` payload. This payload must contain explicit, actionable instructions detailing exactly how the Maker agent should remediate the failure.
