# The Maker-Checker-Approver Pipeline

Evaluating and validating the outputs of multi-agent systems remains a significant challenge. Many platforms default to stochastic language model self-correction loops—often termed a **Generator-Critic pattern**—where a secondary agent reviews the primary agent's output and provides text-based feedback.

## The Fallacy of Stochastic Self-Correction

Frameworks utilizing conversational coordination (like AutoGen and CrewAI) lean heavily on this methodology. However, this approach relies entirely on the probabilistic capability of the secondary language model to detect logical flaws, syntax errors, or schema deviations.

Because both the generator and the critic are susceptible to the identical fundamental failure modes—hallucination, sycophancy, and mathematical inability—stochastic evaluation frequently results in **false positives**, where broken code or invalid JSON payloads are enthusiastically approved by a sycophantic critic agent.

## Deterministic Quality Gates

The CoReason platform fundamentally rejects stochastic self-correction for structural and syntactical validation. Instead, it enforces a rigid **Maker-Checker-Approver** pipeline that natively integrates mathematical and programmatic boundary checks.

### 1. Tier 1 Deterministic Validation (Fail Fast)

Before heavily orchestrating complex tasks, the platform implements a strictly-typed **Tier 1 Validation Registry**. 

If incoming payloads or agent-generated structures fail these core definitions, the pipeline instantly errors out or triggers a deterministic rollback. This completely eliminates wasted LLM tokens processing fundamentally invalid payloads.

### 2. The Maker (Generation)
An isolated sub-agent (the Maker) generates the required artifact, such as Python code, JSON payloads, or SQL queries.

### 3. The Checker (Deterministic Validation)
Rather than passing this artifact to another language model, it is intercepted by a purely deterministic LangGraph node (the Checker). **This node executes zero generative LLM calls.** 

Furthermore, elements like the `jinja2_ast_auditor` are strictly decoupled from the stochastic LLM tool registry, ensuring they act only as rigid evaluation bounds rather than flexible tools.

It runs the artifact against rigid validation boundaries:
- Abstract Syntax Tree (AST) parsers
- Strictly enforced `Pydantic` data validation models
- Isolated code execution sandboxes

### 4. Remediation or The Approver
If the AST check fails or the generated JSON violates the Pydantic boundaries, the Checker node programmatically generates a deterministic error payload and automatically routes the state machine back to the Maker agent for remediation.

Only when the artifact mathematically passes *all* deterministic boundary checks does the system allow it to proceed to an **Approver** (a Project Manager agent or a Human-in-the-Loop) for final semantic approval.

## Structural Integrity First

By enforcing Pydantic type safety and structural integrity before the output is ever subjected to secondary semantic review, the platform guarantees data integrity and completely prevents malformed data from triggering catastrophic downstream actions. Validation is treated as a deterministic software engineering problem rather than a stochastic prompt problem.

## Systemic PM Enforcement

Every Project Manager (PM) agent within the environment (e.g., `frontend_pm`, `backend_pm`, `librarian_pm`, `agent_pm`) is mathematically bound to this paradigm. They do not generate outputs themselves; they strictly orchestrate an internal LangGraph `StateGraph` using native declarative nodes and conditional edges that routes generation tasks to Maker nodes and forcefully halts at Checker nodes until validation passes.

**Note:** Stubs, mocks, and simulated data are strictly prohibited in the Maker agents. All deterministic generation nodes must execute genuine, verifiable tasks to satisfy the Anti-Stub validation checklist.
