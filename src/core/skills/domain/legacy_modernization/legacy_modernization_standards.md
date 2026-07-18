# Legacy Modernization Standards

> **Taxonomy Bucket**: workflow/
> **Scope**: This skill is a construction guide for factory agents that **deconstruct and refactor**
> legacy agentic codebases into modern DeepAgent manifests. It defines how to identify legacy
> antipatterns, produce the LegacyIR schema, and convert patterns to 2026 standards.

---

## 1. Legacy Pattern → Modern Target Mapping

| Legacy Pattern | Detection Signal | Modernized Target |
|---|---|---|
| **Spaghetti Prompting** | Single prompt string > 500 tokens mixing instructions, examples, tool guidelines | **JIT Skill Decomposition**: Split into dedicated `SKILL.md` files cataloged via `skill_registry` with `artifact_types` routing |
| **Free-Text Handoffs** | Agents passing raw strings between each other via `output` or `return` statements | **Strict Pydantic Contracts**: ≤ 3 levels deep, 5–8 parameters wide, passed via typed graph edges |
| **Direct Egress Side-Effects** | `requests.post()`, `open()` for write, `subprocess`, direct DB connections | **MCP Tool Isolation**: Wrap in JSON-RPC tools with zero-trust boundaries, input validation, and provenance |
| **Linear Sequential Pipelines** | Fixed function call chains with no conditional branches or feedback | **Directed Cyclic Graphs (DCGs)**: State loops with feedback nodes, self-correction, and hard circuit breakers |
| **Monolithic Agent Classes** | Single class doing interrogation, computation, AND file writing | **Context Engineering Harness**: Split into supervisor (orchestrator) + sub-agent (deterministic worker) |

---

## 2. LegacyIR Production Rules

When producing the Intermediate Representation:

### Agent Extraction
- Identify every class, function, or configuration block that acts as an "agent"
- Extract the full system prompt text VERBATIM — do not summarize or clean it
- Classify as `supervisor`, `sub-agent`, or `ambiguous` based on behavioral signals
- List all tools/functions the agent calls that produce external side-effects

### Tool Side-Effect Mapping
- Catalog every function that performs I/O: HTTP requests, file writes, DB queries, subprocess calls
- Classify the egress type and risk level
- Record the source file and line number for traceability

### State Graph Reconstruction
- Map the implicit control flow between agents
- Identify handoff types: free_text (string passing), json (structured), function_call (direct invocation)
- Flag any circular dependencies or missing error handlers

### Security Scanning
- Scan for hardcoded credentials using regex patterns for API keys, tokens, passwords
- Flag eval/exec usage as `critical`
- Flag unvalidated user input flowing into prompts as `prompt_injection_surface`

---

## 3. Refactoring Guidelines for Downstream Makers

### For `prompt_engineer` (receiving `agents[].raw_prompt`)
- Decompose spaghetti prompts into role-constrained system prompts
- Add explicit negative constraints ("DO NOT interrogate the user")
- Extract embedded examples into skill documents
- Ensure every modernized prompt enforces evaluate/interrogate/delegate (orchestrator) or deterministic execution (sub-agent)

### For `yaml_compiler` (receiving `agents[]` structure)
- Generate one `agent.yaml` per extracted agent
- Set `name` matching `snake_case` folder convention
- Populate `skill_registry` with appropriate building standards
- Wire `dependencies` based on the reconstructed state graph

### For `fastapi_coder` (receiving `tool_side_effects[]`)
- Wrap each side-effect in a compliant MCP tool with JSON-RPC interface
- Add input validation schemas
- Remove hardcoded credentials — reference Vault/env instead
- Add provenance headers to data-retrieval endpoints

---

## 4. Remediation Loop Protocol

When the `agent_validator` returns FAIL on a modernized artifact:

1. The `agent_pm` extracts `remediation_directives` from the validator's report
2. The failing Maker receives the original IR section + the validator's failure details
3. The Maker regenerates ONLY the failing artifact — no full re-run
77: 4. **Max 3 remediation cycles** — after 3 consecutive FAILs, escalate to the Human PM with the full failure chain
78: 
---

## 5. Refusal Predicate & Negative Constraints

- **When to Halt**: If the legacy codebase relies on fundamentally incompatible architectures (like pure raw string completion endpoints without function calling) that cannot map to the AgentSpec v26 or DeepAgent harness, halt and escalate to the human PM.
- **Negative Constraints**: Do not attempt to summarize or shorten legacy system prompts during the extraction phase. They must be extracted verbatim to preserve intent.
