# Agent Validation Standards

> **Scope**: This skill is used exclusively by the `agent_validator` sub-agent. It contains the formal verification checklists for validating agent definitions produced by the factory. The validator loads this skill and runs each check against the submitted artifact. Pass/fail only — no construction guidance (that lives in `building/agent_building_standards.md`).

---

## Input Contract

The validator receives a completed agent definition payload containing:
- `agent.yaml` content
- `orchestrator.py` content (if applicable)
- Agent folder path
- Agent type declaration (`supervisor` or `sub-agent`)

## Validation Checklist

### V1. Type Correctness
- [ ] Is the agent typed as `supervisor` or `sub-agent`?
- [ ] Does the `type` field exist and contain exactly one of the two allowed values?
- [ ] **FAIL** if type is missing, empty, or contains any other value

### V2. Behavioral Alignment
- [ ] If `type: supervisor` — does the system prompt include evaluate/interrogate/delegate behavior?
- [ ] If `type: sub-agent` — does the system prompt include "DO NOT interrogate the user" or equivalent constraint?
- [ ] **FAIL** if the system prompt contradicts the declared type

### V3. No Mixed Concerns
- [ ] If `type: supervisor` — does the system prompt contain any code generation, file writing, or computational execution instructions?
- [ ] If `type: sub-agent` — does the system prompt contain any phrases like "ask the user", "clarify with", "request more info", or "interrogate"?
- [ ] **FAIL** if an orchestrator does execution work, or a sub-agent does interrogation

### V4. Namespace Match
- [ ] Does the `name` field exactly match the `snake_case` folder name?
- [ ] Example: folder `yaml_compiler/` → `name: "yaml_compiler"`
- [ ] **FAIL** if there is any mismatch (case, hyphens, aliases, creative naming)

### V5. Dependencies Declared
- [ ] Are all sub-agents or upstream agents listed in the `dependencies` field?
- [ ] Does the system prompt reference agents that are NOT in `dependencies`?
- [ ] **FAIL** if the prompt mentions delegation to agents not listed as dependencies

### V6. Skills Declared
- [ ] Does the agent reference skills via the `skills` field?
- [ ] Do the referenced skill paths resolve to existing files?
- [ ] **FAIL** if skills are referenced in the prompt but not declared in the `skills` field

### V7. Human Escalation Path
- [ ] For `type: supervisor` agents — does the system prompt define an escalation path for decisions outside the agent's domain?
- [ ] **WARN** (not fail) if no escalation path is defined — flag for human review

### V8. System Prompt Completeness
- [ ] Does the system prompt define the agent's role clearly?
- [ ] Does it reference the agent's skills and tools?
- [ ] Does it include explicit constraints (what the agent must NOT do)?
- [ ] **WARN** if constraints are missing

## Output Contract

The validator returns a structured result:

```json
{
  "status": "PASS" | "FAIL",
  "agent_name": "string",
  "checks": [
    {
      "id": "V1",
      "name": "Type Correctness",
      "status": "PASS" | "FAIL" | "WARN",
      "detail": "string"
    }
  ],
  "summary": "string"
}
```

> **Rule**: If ANY check returns `FAIL`, the overall status is `FAIL`. The artifact MUST NOT be written to disk. Return the full report to the agent_pm for remediation routing.
