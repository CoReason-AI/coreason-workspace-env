# Legacy Validation Standards

> **Scope**: This skill is used exclusively by the `agent_validator` sub-agent. It contains the
> formal verification checklists for validating the output of a legacy modernization workflow.
> The validator loads this skill when the artifact_type is `legacy_ir` and runs each check.

---

## Input Contract

The validator receives either:
- A `LegacyIR` JSON object (output of the deconstructor, before Maker consumption)
- A modernized artifact set (output of the Makers, before disk write)

## Phase 1: IR Validation (Post-Deconstruction)

### V1. Schema Compliance
- [ ] Does the IR conform to the `LegacyIR` Pydantic schema?
- [ ] Are all required fields present and non-empty?
- [ ] **FAIL** if schema validation fails

### V2. Agent Extraction Completeness
- [ ] Does `agents[]` contain at least one entry?
- [ ] Does every entry have a non-empty `raw_prompt`?
- [ ] Does every entry have a valid `type_guess`?
- [ ] **FAIL** if any agent entry is incomplete

### V3. Security Scan Exhaustiveness
- [ ] Were all Python files in the repository scanned?
- [ ] Does `raw_file_count` match the actual file count?
- [ ] Are `security_flags[]` populated (even if empty — must be present)?
- [ ] **FAIL** if scan coverage is incomplete

### V4. Side-Effect Coverage
- [ ] Does every function performing I/O appear in `tool_side_effects[]`?
- [ ] Is `egress_type` correctly classified for each?
- [ ] **WARN** if side-effects seem under-reported relative to file count

## Phase 2: Modernized Artifact Validation (Post-Refactoring)

### V5. No Legacy Antipattern Leakage
- [ ] Do any modernized system prompts still contain spaghetti patterns (> 500 tokens of mixed concerns)?
- [ ] Do any agent YAMLs use free-text handoffs instead of typed schemas?
- [ ] Are there any remaining direct egress calls outside MCP tool boundaries?
- [ ] **FAIL** if any legacy antipattern survives modernization

### V6. Credential Sanitization
- [ ] Do any modernized files contain hardcoded API keys, tokens, or passwords?
- [ ] Are all credentials referenced via environment variables or Vault paths?
- [ ] **FAIL** if any hardcoded credential is found — this is a CISO-blocking issue

### V7. MCP Tool Compliance
- [ ] Does every extracted side-effect have a corresponding MCP tool wrapper?
- [ ] Does every MCP tool have input validation and provenance headers?
- [ ] **FAIL** if unprotected side-effects remain

### V8. Skill Registry Completeness
- [ ] Does every modernized agent.yaml have a valid `skill_registry` (not the deprecated `skills` array)?
- [ ] Do all `artifact_types` in the registry reference canonical types?
- [ ] **FAIL** if any agent uses the deprecated format

### V9. State Graph Integrity
- [ ] Does the modernized dependency graph match the original state graph edges?
- [ ] Are all inter-agent connections explicitly declared in `dependencies`?
- [ ] **WARN** if edges are lost during modernization

## Output Contract

```json
{
  "status": "PASS" | "FAIL",
  "phase": "ir_validation" | "artifact_validation",
  "checks": [
    {
      "id": "V1",
      "name": "Schema Compliance",
      "status": "PASS" | "FAIL" | "WARN",
      "detail": "string"
    }
  ],
  "summary": "string"
}
```
