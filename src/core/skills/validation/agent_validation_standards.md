# Agent Validation Standards

> **Taxonomy Bucket**: validation/
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

- [ ] Does the agent import schemas from coreason_manifest instead of declaring them locally?
- [ ] Does the agent use uuid.uuid7() natively instead of uuid.uuid4() for primary keys?
- [ ] **FAIL** if local schema duplication or uuid.uuid4() is found.

### V9. Jinja2 Decoupling Pattern
- [ ] Does the agent attempt to write Markdown files containing computational or empirical data directly inline (e.g., via f-strings or LLM generation)?
- [ ] Does the agent adhere to the 3-step Jinja2 Decoupling Pattern (Emitter script -> `.md.j2` Template -> Compiler script) for empirical data?
- [ ] **FAIL** if any Markdown reports with computed data are not utilizing the Jinja2 decoupling pattern.

### V10. Omnigent Compatibility
- [ ] Does the agent explicitly define an `executor` block (with `harness` and `model`) OR an `llm_config` referencing a configured LLM component?
- [ ] Does the agent explicitly declare `async: true` and `cancellable: true`?
- [ ] If the agent references local filesystem or shell tools (e.g. `local_fs_writer`, `terminal`), does it define an `os_env` block?
- [ ] **FAIL** if both `executor` and `llm_config` are missing or malformed, or if `os_env` is missing when required.

### V11. Causal Inference
- [ ] If the agent performs analysis, estimation, or structural modeling — does it utilize causal inference (e.g., the `dowhy` library) rather than relying strictly on correlational heuristics?
- [ ] **WARN** if the agent relies on correlation without evaluating causal methodologies.

### V12. Neuro-Symbolic Validation
- [ ] For high-stakes domains — does the agent rely on formal, executable models (e.g., SMT solvers, SHACL graphs) for final deduction instead of pure LLM text output?
- [ ] **WARN** if high-stakes deduction relies purely on unverified LLM generation.

### V13. Scientific Frameworks (Self-Reflection)
- [ ] For hypothesis generation or research pipelines — does the agent implement closed-loop Self-Reflection and Critique Loops?
- [ ] **WARN** if the research pipeline lacks automated feedback and critique loops.

### V14. Persistent Structured Workspaces
- [ ] For complex, multi-hop reasoning tasks — does the agent externalize reasoning state into Structured CoT Artifacts (e.g., dynamically updated tables or Knowledge Graphs)?
- [ ] **WARN** if the agent relies on long, unstructured Chain-of-Thought text blocks.

### V15. Native Reasoning Models
- [ ] Does the agent leverage frontier reasoning models (e.g., DeepSeek-R1, OpenAI o3) with high test-time compute allocations for complex Tree-of-Thoughts exploration?
- [ ] **WARN** if a standard model is used for tasks requiring deep, multi-step decomposition without explicit justification.

### V16. Analogical Prompting
- [ ] For zero-shot reasoning tasks, does the agent's prompt utilize Analogical Prompting (self-generating 3-5 exemplars) when static few-shot examples are unavailable?
- [ ] **WARN** if the agent attempts zero-shot reasoning without analogical scaffolding.

### V17. Explicit Structural Mapping
- [ ] When performing analogical transfer, does the agent explicitly externalize the relational structure into a mapping artifact (e.g., JSON/YAML graph) before synthesizing the answer?
- [ ] **FAIL** if the agent relies on unstructured text for analogy without formal structural mapping.

### V18. Archetypal Anchoring
- [ ] For complex orchestrators, does the system prompt invoke a specific, coherent behavioral persona (an "archetype") early in the context window to stabilize the latent space?
- [ ] **WARN** if the orchestrator lacks a behavioral anchor before deep reasoning loops.

### V19. Dialectical Synthesis
- [ ] For ideation, design, or hypothesis generation tasks, does the agent employ Dialectical Reasoning (Thesis -> Antithesis -> Synthesis)?
- [ ] **WARN** if creative or ambiguous tasks lack a dialectical critique mechanism.

### V20. Epidemiological Causal Inference (Hill's Criteria)
- [ ] For health/epidemiological risks, does the agent evaluate associations against Bradford Hill criteria and construct DAGs?
- [ ] **WARN** if the agent infers medical causality from correlation without formal framework application.

### V21. Counterfactual Simulation (Do-Calculus)
- [ ] When proposing clinical/PHM interventions, does the agent simulate `do-interventions` via a causal engine to rank treatment effects?
- [ ] **WARN** if interventions are recommended purely on LLM token probabilities without causal simulation.

### V22. Multi-Model Consensus
- [ ] For GxP or high-risk tasks, does the agent use a Consortium Pattern with a Governance Agent synthesizing multiple models' outputs?
- [ ] **WARN** if a single LLM is relied upon for high-risk regulatory decisions.

### V23. Abductive Root-Cause Isolation
- [ ] For diagnostics, does the agent use abductive reasoning over a causal graph to identify the most plausible root cause from symptoms?
- [ ] **WARN** if the agent attempts root cause analysis without abductive logic or a defined causal graph.

### V24. Glass Box Traceability
- [ ] For regulated (GxP/FDA) environments, does the agent explicitly document assumptions, constraints, and domain boundaries (e.g., `assumptions_and_constraints` JSON block) before acting?
- [ ] **FAIL** if the agent operates as a black box without explicit, structured traceability in regulated domains.

### V25. Bayesian Belief Updating (Orchestration)
- [ ] For orchestrators managing high-uncertainty routing or diagnostics, does the system prompt mandate a Bayes-consistent tracking of prior and posterior beliefs?
- [ ] **WARN** if the orchestrator resolves complex uncertainty without tracking an explicit probabilistic world model.

### V26. LangChain v1 Migration Adherence
- [ ] Does the payload import from `langchain-community`?
- [ ] Does the payload use `AgentExecutor`, `ConversationBufferMemory`, or legacy Chains (`LLMChain`)?
- [ ] Does the payload use `langgraph.prebuilt.create_react_agent` instead of `langchain.agents.create_agent`?
- [ ] **FAIL** if any deprecated LangChain abstractions or community packages are present.

### V27. Open-Source Observability
- [ ] Does the payload contain telemetry endpoints or SDK imports pointing to `LangSmith`?
- [ ] **FAIL** if `LangSmith` is referenced. `Langfuse` is the strictly mandated standard.

### V28. Native Semantic Memory
- [ ] Does the payload attempt to manually instantiate external vector databases (e.g., `langchain-qdrant`, `pinecone`)?
- [ ] **FAIL** if the agent manually wires vector stores. Long-term memory MUST use LangGraph's native `Annotated[BaseStore, InjectedStore()]` pattern exclusively.

### V29. DeepAgents API Contract
- [ ] Does the payload rely on deprecated `deepagents < 0.6.0` abstractions like `ls_info` or `ASYNC_GREP_TIMEOUT`?
- [ ] Does the payload use legacy pre-model/post-model hooks instead of Middleware (`before_model`, `after_model`)?
- [ ] **FAIL** if legacy deepagents contracts are referenced.
