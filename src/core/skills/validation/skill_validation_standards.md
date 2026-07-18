# Skill Validation Standards

> **Taxonomy Bucket**: validation/
> **Scope**: This skill is used exclusively by the `agent_validator` sub-agent. It contains the formal verification checklists for validating agentic Skills (SOPs) produced by the factory. Pass/fail only — no construction guidance (that lives in `building/skill_building_standards.md`).

---

## Input Contract

The validator receives a completed skill definition containing:
- Skill file content (markdown or Python)
- Input/output schema definitions
- Integration contract details

## Validation Checklist

### V1. Single Responsibility
- [ ] Does the skill perform exactly one atomic operation?
- [ ] Are there multiple distinct operations bundled in one file?
- [ ] **FAIL** if the skill contains more than one primary operation

### V2. Input/Output Schema Present
- [ ] Does the skill define a strict input schema (Pydantic or equivalent)?
- [ ] Does the skill define a strict output schema?
- [ ] **FAIL** if either schema is missing or loosely typed (e.g., `Dict[str, Any]`)

### V3. Schema Depth & Width
- [ ] Is the output schema `≤ 3` levels deep?
- [ ] Are parameter counts limited to 5-8 per level?
- [ ] **FAIL** if schema exceeds depth or width limits

### V4. Refusal Predicate
- [ ] Does the skill define an explicit failure/refusal condition?
- [ ] Does it return a structured error state (e.g., `NOT_FOUND`) when required data is missing?
- [ ] **FAIL** if the skill can silently proceed with missing data or fabricate results

### V5. Negative Constraints
- [ ] Does the skill explicitly define what the LLM is forbidden from doing?
- [ ] Are role-bleed risks addressed (e.g., a data-extraction skill must not make domain judgments)?
- [ ] **WARN** if negative constraints are absent

### V6. Idempotency
- [ ] Can the skill be run twice safely without compounding side effects?
- [ ] **FAIL** if running the skill twice produces inconsistent results or duplicate side effects

### V7. Integration Contract
- [ ] Is the skill labeled as `Read-Only` or `State-Mutating`?
- [ ] If state-mutating, does it mandate WAL or Saga compensation patterns?
- [ ] Is the skill declared as stateless or stateful?
- [ ] **WARN** if integration contract is missing

### V8. Progressive Disclosure
- [ ] Does the skill begin with a semantic discovery abstract?
- [ ] Is the abstract concise enough for JIT loading without pulling the full skill?
- [ ] **WARN** if discovery abstract is missing

### V9. Provenance (for data-retrieval skills)
- [ ] If the skill fetches factual data, does the output include `provenance_receipts`?
- [ ] **FAIL** if factual data is returned without source attribution

### V10. Path Portability
- [ ] Are all file paths relative and dynamically resolved?
- [ ] Are there any hardcoded absolute paths or OS-specific separators?
- [ ] **FAIL** if absolute paths or OS-specific separators are found

### V11. No Mock Data
- [ ] Does the skill produce real outputs from real execution paths?
- [ ] Are there any simulated data points, mock charts, or proof-of-concept fakes?
- [ ] **FAIL** if mock/simulated data is present

## Output Contract

```json
{
  "status": "PASS" | "FAIL",
  "artifact_name": "string",
  "checks": [
    {
      "id": "V1",
      "name": "Single Responsibility",
      "status": "PASS" | "FAIL" | "WARN",
      "detail": "string"
    }
  ],
  "summary": "string"
}
```

> **Rule**: If ANY check returns `FAIL`, the overall status is `FAIL`. The artifact MUST NOT be written to disk.
