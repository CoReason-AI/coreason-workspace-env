
# SKILL.md - Clinical Definition Synthesis

## Semantic Discovery Abstract
- **Goal**: Synthesize a single, naturalized clinical definition from raw authoritative dictionaries (MSH, NCI, HPO).
- **Causal Affordance**: Triggered immediately after exact definitions are retrieved by the deterministic ontology fetcher to provide human-readable context to downstream agents and users.
- **Epistemic Bounds**: The LLM must not invent clinical symptoms, severity markers, or pathophysiology that were not present in the raw definitions.
- **MCP Routing Triggers**: Synthesis, Definitions, MSH, NCI, HPO, Naturalized Text

### Metadata Block
- **Skill ID**: `pv/clinical_definition_synthesis`
- **Domain**: Pharmacovigilance / Medical Informatics
- **Primary User**: Safety Scientist
- **Associated MCP Tools**: `sequentialthinking`
- **Component Type**: Tool (Deterministic Transform)
- **EU AI Act Risk Category**: Limited
- **Human Oversight Modality**: HOTL (Human-in-the-Loop)
- **Explainability Method**: Evidence-Anchored

## Integration Contract
- **Compute Constraints**: Generative synthesis strictly constrained to concatenation and naturalization of input vocabularies without hallucination.
- **Side-Effect Risk**: Read-Only semantic processing. No state mutation.
- **SDK Decoupling**: Text naturalization logic operates independently of any orchestration SDK.

## Intent & Trigger
- **Atomic Goal**: Take raw dictionary definitions and safely rewrite them into a single, cohesive clinical paragraph.
- **Trigger Condition**: Triggered immediately after `ontological_graph_and_crosswalk_retrieval` completes in Phase 1.

## Required Inputs & Type Safety
The agent accepts a list of UMLS CUI profiles containing raw dictionary definitions:

### Input Schema (Strict JSON, ≤ 3 levels deep)
```json
{
  "umls_profiles": [
    {
      "umls_cui": "str",
      "definitions": {
        "msh_raw": "str | null",
        "nci_raw": "str | null",
        "hpo_raw": "str | null"
      }
    }
  ]
}
```

## Execution Framework & Output Contract
AGENT INSTRUCTION: You must output a JSON object matching the exact schema structure below. Do not use different key names. Do not add conversational text.

### Mandatory Output Schema
```json
{
  "synthesized_definitions": [
    {
      "umls_cui": "str",
      "synthesized_naturalized_definition": "str",
      "provenance_receipts": {
        "msh": true,
        "nci": true,
        "hpo": true
      }
    }
  ]
}
```

### Formatting Rules:
- **`synthesized_naturalized_definition`**: A single, clean clinical paragraph combining the MSH, NCI, and HPO inputs. If all inputs are empty/null, this field MUST be exactly `"NO_DEFINITION_AVAILABLE"`.
- **`provenance_receipts`**: A boolean map indicating which source definitions were non-empty. Use the exact lowercase keys: `msh`, `nci`, and `hpo`.

## Negative Constraints & Guardrails
- **Refusal Predicate**: You are strictly forbidden from guessing definitions if the input fields are empty/null. If all three are null, output `"NO_DEFINITION_AVAILABLE"`.
- **Anti-Citation Rule**: Explicitly forbid the agent from casually citing human-facing textbooks, consulting literature, or non-peer-reviewed sources. Enforce native mathematical execution instead.
- **Provenance Rule**: DO NOT return external or retrieved factual data without attaching strict provenance metadata (e.g., citation IDs, source JSON blocks) to allow downstream cryptographic verification.
- **Definition Guardrails**: The agent must not invent clinical symptoms, treatments, or pathophysiology that were not explicitly present in the provided raw texts.
```

