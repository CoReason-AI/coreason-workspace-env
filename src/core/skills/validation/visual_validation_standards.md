# Visual Validation Standards

> **Taxonomy Bucket**: validation/
> **Scope**: This skill is used exclusively by the `agent_validator` sub-agent. It contains the formal verification checklists for validating architecture diagrams and workflow visualizations produced by the factory. Pass/fail only — no construction guidance (that lives in `building/visual_building_standards.md`).

---

## Input Contract

The validator receives a completed diagram/visualization containing:
- Mermaid graph definition
- Node definitions
- Edge definitions with annotations
- Shared Goal Narrative (if applicable)

## Validation Checklist

### V1. Deterministic Representation
- [ ] Does the diagram represent actual state transitions and topological structures?
- [ ] Are there any vague conversational flows or abstract "AI does things" nodes?
- [ ] **FAIL** if the diagram contains non-deterministic or abstract representations

### V2. Node Symbology Compliance
- [ ] Do triggers/entry points use square brackets `[]`?
- [ ] Do agents use rounded rectangles `()`?
- [ ] Do database/system integrations use cylinders `[()]`?
- [ ] Do decision gates use rhombuses `{}`?
- [ ] **FAIL** if nodes use incorrect shapes for their function

### V3. Node Labels
- [ ] Are all agent nodes prefixed with their structural domain (e.g., `Supervisor:`, `Worker:`, `Shared Service:`)?
- [ ] Are there any generic labels like "AI Agent" or "System"?
- [ ] **FAIL** if any node has a generic, non-role-specific label

### V4. Edge Symbology Compliance
- [ ] Do standard handoffs use solid lines (`-->`)?
- [ ] Do executive mandates use thick lines (`==>`)?
- [ ] Do debate/escalation flows use dashed lines (`-.->`)?
- [ ] **FAIL** if edge styles don't match their semantic meaning

### V5. Edge Annotations
- [ ] Does every edge between agents define an action (e.g., "Delegate Compilation")?
- [ ] Does every edge include a protocol annotation (e.g., `(mcp: sequentialthinking)`)?
- [ ] **FAIL** if any edge is unbound (missing action or protocol)

### V6. Shared Goal Narrative
- [ ] Is the diagram preceded by a `## The Multi-Agentic Shared Goal` section?
- [ ] Does the narrative explain agent coordination, pipeline type, and shared objective?
- [ ] **WARN** if the shared goal narrative is missing

### V7. Dark Theme
- [ ] Does the Mermaid graph include `%%{init: {'theme': 'dark'}}%%`?
- [ ] **WARN** if dark theme initialization is missing

### V8. Forbidden Terminology
- [ ] Are there any instances of deprecated terms: "MAR", "Downward MAR", "Strategic Silence", "Hollow Data Plane"?
- [ ] **FAIL** if any deprecated terminology is found

### V9. No Conversational Verbs
- [ ] Are edge labels using structural commands ("Delegate", "Validate", "Synthesize")?
- [ ] Are there any human-centric verbs ("Ask about", "Talk to", "Discuss")?
- [ ] **FAIL** if conversational verbs are used on edges

## Output Contract

```json
{
  "status": "PASS" | "FAIL",
  "artifact_name": "string",
  "checks": [
    {
      "id": "V1",
      "name": "Deterministic Representation",
      "status": "PASS" | "FAIL" | "WARN",
      "detail": "string"
    }
  ],
  "summary": "string"
}
```

> **Rule**: If ANY check returns `FAIL`, the overall status is `FAIL`. The artifact MUST NOT be written to disk.
