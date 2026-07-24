# Deterministic Tool Usage Audit Standard

**Category**: `validation`
**Description**: Audits agent system prompts, skills, and python code to ensure deterministic operations (calculations, math, static analysis, regex parsing, SQL queries) use deterministic tools instead of probabilistic LLM token output.

---

## Audit Rules

### Rule 1: No LLM Arithmetic / Math Calculations
- **Violation**: System prompts instructing LLMs to manually compute mathematical formulas, tax rates, or financial totals in text.
- **Remediation**: Must delegate math calculations to deterministic Python tools (`calculate_vat`, `numpy`, `pandas`, `math_tool`).

### Rule 2: Static Analysis & AST Parsing
- **Violation**: Asking LLMs to parse JSON or Python AST using plain text regex when standard library tools (`ast`, `json.loads`) are available.
- **Remediation**: Force deterministic Python tool execution for structural parsing.

### Rule 3: Zero Hardcoded Credentials & Injection Risks
- **Violation**: Prompts containing raw API keys, passwords, or un-sanitized user string concatenation without parameterized injection guards.
- **Remediation**: Use HashiCorp Vault tokens and parameterized inputs.
