# MCP Validation Standards

> **Scope**: This skill is used exclusively by the `agent_validator` sub-agent. It contains the formal verification checklists for validating MCP server specifications produced by the factory. Pass/fail only — no construction guidance (that lives in `building/mcp_building_standards.md`).

---

## Input Contract

The validator receives a completed MCP server specification containing:
- Server configuration (transport, auth, tools list)
- Tool definitions (input/output schemas)
- Integration contract details

## Validation Checklist

### V1. Zero-Trust Boundary
- [ ] Does the specification route ALL external interactions through MCP Tools?
- [ ] Are there any instances of direct API calls, raw SQL, or `requests.get()` patterns?
- [ ] **FAIL** if any agent-to-external-system interaction bypasses the MCP boundary

### V2. Integration Contract Present
- [ ] Does the specification declare a transport protocol (`stdio` or `sse`)?
- [ ] Does it list all required environment variables for authentication?
- [ ] Does it define rate limits and concurrency constraints?
- [ ] **FAIL** if transport protocol is missing
- [ ] **WARN** if rate limits or auth requirements are undocumented

### V3. No Hardcoded Credentials
- [ ] Scan the specification for hardcoded API keys, passwords, tokens, or connection strings
- [ ] All credentials must reference environment variables or secrets manager paths
- [ ] **FAIL** if any credential appears as a literal value

### V4. Provenance / Receipt Pattern
- [ ] For data-retrieval tools: does the output schema include a `provenance_receipts` field?
- [ ] Does every tool that returns factual data attach source URIs or citation IDs?
- [ ] **FAIL** if a data-retrieval tool returns raw text without provenance metadata

### V5. Tool Schema Compliance
- [ ] Does each tool have a single, clear responsibility?
- [ ] Are input schemas strict Pydantic models (no arbitrary dicts)?
- [ ] Are output schemas `≤ 3` levels deep with 5-8 parameters max?
- [ ] Are error responses structured and actionable?
- [ ] **FAIL** if schemas exceed depth/width limits or use untyped parameters

### V6. Idempotency for State-Mutating Tools
- [ ] Do state-mutating tools enforce caller-supplied `idempotency_keys`?
- [ ] **FAIL** if a state-mutating tool has no idempotency mechanism

### V7. No Simulated Tools
- [ ] Are there any tool implementations returning simulated/mock output?
- [ ] All tools must execute real integration paths
- [ ] **FAIL** if any tool contains `return "Simulated output"` or equivalent

## Output Contract

```json
{
  "status": "PASS" | "FAIL",
  "artifact_name": "string",
  "checks": [
    {
      "id": "V1",
      "name": "Zero-Trust Boundary",
      "status": "PASS" | "FAIL" | "WARN",
      "detail": "string"
    }
  ],
  "summary": "string"
}
```

> **Rule**: If ANY check returns `FAIL`, the overall status is `FAIL`. The artifact MUST NOT be written to disk.
