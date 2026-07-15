# Writing Validation Rules

Validation rules are deterministic scripts executed by the Checker agents (e.g., `agent_validator`) to evaluate artifacts produced by Makers.

## How to Write a Rule

1.  **Define the Metric:** What exactly are you measuring? (e.g., "AST contains no `eval()` calls").
2.  **Write the Check:** Write a Python function that takes the artifact payload and returns a boolean pass/fail and a detailed error message if it fails.
3.  **Register the Rule:** Place the rule in `src/core/skills/validation/` so the Checker agent can discover it.

Validation rules act as the physical enforcement mechanism for the policies outlined in `AGENTS.md`.
