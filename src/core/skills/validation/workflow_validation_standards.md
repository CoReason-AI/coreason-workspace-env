# Workflow Validation Standards

> **Taxonomy Bucket**: validation/
> **Scope**: This skill is used exclusively by the `agent_validator` sub-agent. It contains the formal verification checklists for validating workflow specifications produced by the factory. Pass/fail only — no construction guidance (that lives in `building/workflow_building_standards.md`).

---

## Input Contract

The validator receives a completed workflow specification containing:
- Workflow topology definition (graph structure)
- Node definitions (agents, tools, decision gates)
- Edge definitions (handoff schemas, protocols)
- Integration contract

## Validation Checklist

### V1. Builder-Validator-Approver Separation
- [ ] Does the workflow separate drafting, validation, and approval into distinct agents?
- [ ] Is any single agent acting as both Builder AND Validator?
- [ ] **FAIL** if the same agent drafts and validates its own output

### V2. Topology Type Declared
- [ ] Does the integration contract declare the topology type (DCG, Sequential, Fan-Out/Join)?
- [ ] **FAIL** if topology type is undeclared

### V3. Feedback Loops Have Circuit Breakers
- [ ] Does every cyclic route define a maximum iteration count?
- [ ] Are retry limits explicit (not implicit/unbounded)?
- [ ] **FAIL** if any feedback loop has no circuit breaker or retry limit

### V4. Handoff Schema Compliance
- [ ] Does every edge between agents have a defined Pydantic handoff schema?
- [ ] Are handoff schemas `≤ 3` levels deep with 5-8 parameters?
- [ ] **FAIL** if any edge lacks a schema or uses unstructured data
- [ ] **FAIL** if schemas exceed depth/width limits

### V5. No Conversational Fluff
- [ ] Are inter-agent data handoffs strictly structured (Pydantic/JSON)?
- [ ] Are there any free-text or conversational data exchanges between nodes?
- [ ] **FAIL** if agents "chat" with each other using unstructured text

### V6. Context Window Discipline
- [ ] Does each node receive only the data required for its specific task?
- [ ] Is the full workflow history passed to any node?
- [ ] **WARN** if nodes receive excessive context beyond their task scope

### V7. Tool Node Encapsulation
- [ ] Are external API calls routed through MCP Tool Nodes?
- [ ] Are there any agents directly calling external APIs?
- [ ] **FAIL** if any agent bypasses the MCP tool layer

### V8. State Persistence Declared
- [ ] Does the integration contract define state persistence requirements (ephemeral or WAL)?
- [ ] **WARN** if state persistence is undeclared

### V9. Provenance Chain
- [ ] For workflows producing authoritative outputs: does every factual-data node attach provenance metadata?
- [ ] Does the final node run an integrity check on the provenance chain?
- [ ] **WARN** if provenance chain is not enforced (may be acceptable for non-authoritative workflows)

### V10. Concurrency Model Declared
- [ ] Does the integration contract define whether nodes execute in parallel or synchronously?
- [ ] **WARN** if concurrency model is undeclared

## Output Contract

```json
{
  "status": "PASS" | "FAIL",
  "artifact_name": "string",
  "checks": [
    {
      "id": "V1",
      "name": "Builder-Validator-Approver Separation",
      "status": "PASS" | "FAIL" | "WARN",
      "detail": "string"
    }
  ],
  "summary": "string"
}
```

> **Rule**: If ANY check returns `FAIL`, the overall status is `FAIL`. The artifact MUST NOT be written to disk.
