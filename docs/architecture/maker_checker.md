# Maker-Checker-Approver Pipeline

The CoReason agent factory operates on a strict **Maker-Checker-Approver** pipeline. This ensures that no agent can unilaterally push code, schemas, or configurations without rigorous, deterministic validation.

## Roles

1. **Makers (The Builders)**
    - *Examples:* `prompt_engineer`, `yaml_compiler`
    - *Function:* These agents accept requirements from the Orchestrator (PM) and generate the raw artifacts (e.g., `agent.yaml` files, Python scripts).
    - *Constraints:* They cannot merge code or write directly to production paths. They output proposals.

2. **Checkers (The Validators)**
    - *Examples:* `agent_validator`
    - *Function:* The Checker intercepts the Maker's proposal and executes deterministic tests against it. It reads the validation standards from `src/core/skills/validation/` and runs static analysis, Pydantic validation, or AST checks.
    - *Constraints:* The Checker does not fix the code; it only scores it and generates an error report if it fails.

3. **Approvers (The PMs)**
    - *Examples:* `agent_pm`
    - *Function:* The PM reviews the Checker's report. If it passes, the PM approves the disk write. If it fails, the PM routes the error report back to the Maker for remediation.

This tripartite manifold guarantees that stochastic LLM generations are always caught by deterministic mathematical boundaries before taking effect.
