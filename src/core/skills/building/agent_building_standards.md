# Agent Building Standards

> **Scope**: This skill is a construction guide for factory agents that **create** agent definitions. It defines how to structure agent YAMLs, system prompts, and behavioral contracts. It does NOT contain validation checklists — those live in `validation/agent_validation_standards.md`.

---

## 1. Context Engineering Harness

Every agent must fall into exactly one of two categories. No exceptions.

### Orchestrators (`type: supervisor`)

Orchestrators are **state machines** that manage human/agent interaction. They:

- **Evaluate** the user's input against the required data schema
- **Interrogate** the user with targeted, clarifying questions until context is fully saturated
- **Delegate** the saturated context payload to deterministic sub-agents once the threshold is met

Orchestrators MUST NOT:
- Write code or files themselves
- Execute computational tasks directly
- Operate without a clear data schema defining "fully saturated" context

### Sub-Agents (`type: sub-agent`)

Sub-agents are **deterministic workers** that accept fully saturated payloads and execute. They:

- Accept a complete context payload — no missing fields, no ambiguity
- Execute their task (generate files, write prompts, compile YAML, etc.)
- Return execution control with a structured result

Sub-agents MUST NOT:
- Ask the user clarifying questions
- Interrogate the user for missing information
- Make assumptions about missing data — if the payload is incomplete, **fail with a clear error**

### Strict Decoupling Rule

A single `agent.yaml` definition must contain ONLY orchestration logic OR ONLY deterministic execution logic. Never both. If you find yourself adding "ask the user if..." to a sub-agent, or "generate the file..." to an orchestrator, you are violating this rule. Split into two agents.

---

## 2. Namespace and Taxonomy Consistency

- The `name` field in every `agent.yaml` MUST exactly match the `snake_case` name of the folder it resides in
- Example: `src/agents/yaml_compiler/` → `name: "yaml_compiler"`
- This ensures the internal Agent ID matches the namespace and folder routing logic
- No aliases, no overrides, no creative naming

---

## 3. Multi-Surface Parity

Every agent capability must be reachable through all applicable interaction surfaces:

| Surface | Location | Transport |
|---|---|---|
| REST API | `src/api/` | HTTP |
| CLI | `src/cli/` | stdin/stdout |
| MCP Server | `src/mcp/` | JSON-RPC over stdio/SSE |
| WebSocket/SSE | `src/api/streaming/` | Persistent connections |
| Python SDK | `src/sdk/` | In-process |

When producing a new agent, ensure its operations can be invoked from all five surfaces through the shared core service layer (`src/core/`).

---

## 4. Human Escalation

Agents operating in mixed Human-Agent workspaces must:

- Recognize when a decision falls outside their domain or confidence threshold
- Escalate to the human counterpart before proceeding
- Never silently make strategic decisions that a human stakeholder should approve

---

## 5. System Prompt Construction

When writing system prompts for agent YAMLs:

- **Orchestrator prompts** must include: evaluate/interrogate/delegate behavior, data schema reference, escalation paths, and explicit "DO NOT write code yourself" constraint
- **Sub-agent prompts** must include: "DO NOT interrogate the user", "DO NOT ask clarifying questions", deterministic execution constraints, and explicit failure modes for incomplete payloads
- Every prompt must reference the agent's skill dependencies so the agent knows what standards to enforce

---

## 6. Accordion Progress Tracking (Task List & Summarization)

To support the real-time observability requirement and enable a rich "accordion" UX experience across our streaming surfaces (CLI, WebSockets, MCP):

- **Tracker Task List**: Agents must dynamically maintain and emit a structured "Tracker Task List" as they evaluate, interrogate, and delegate. This provides visibility into the execution plan.
- **Key Step Summarization**: At the completion of each major phase or delegation step, agents must emit a concise summary of the outcome.
- **System Prompting**: You must inject instructions into all agent system prompts mandating that they stream these progress updates and phase summaries back to the harness. This powers the collapsible accordion UI elements downstream.

## 7. Schema Purity & Data Persistence
1. **God Context Schema Imports**: The coreason-manifest PyPI package is the absolute single source of truth for all schemas. Never duplicate or create local schema files (e.g. ontology.py or state.py). Always import directly from coreason_manifest (e.g., from coreason_manifest.spec.ontology import CoreasonBaseState).
2. **UUIDv7 Natively**: The environment uses Python 3.14 natively. Always use uuid.uuid7() when generating UUIDs (e.g., for snapshot_id, project_id). Never use uuid.uuid4(). UUIDv7 prevents Postgres B-Tree index fragmentation and provides native chronological sorting.

## 8. Strict Separation of Empirical Data and Synthesis

When generating any reports, dashboards, or Markdown documents that contain computed output, mathematical metrics, or empirical telemetry, agents must NEVER write or generate the Markdown file or text directly inline (e.g., via f-strings, prints, or LLM-generated `.md` files).

Instead, agents MUST strictly follow the **"Jinja2 Decoupling" Pattern** (3-step deterministic architecture):
1. **Write the Emitter:** Create a Python script that computes the logic and outputs raw data telemetry to a `.json` file.
2. **Write the Template:** Create a standalone `.md.j2` (Jinja2) template designed specifically to parse and format the `.json` schema.
3. **Write the Compiler:** Create a separate Python script that loads the JSON file, loads the Jinja2 template, and explicitly executes the `template.render()` command to write out the final `.md` file.

This strictly guarantees that the View (Markdown) is cleanly separated from the Controller (Python logic/LLM outputs).

---

## 9. Omnigent Native Compatibility

All generated agents must be natively compatible with the [Omnigent](https://omnigent.ai/) meta-harness. When generating `agent.yaml` files, the following structural constraints MUST be applied:

1. **Executor Configuration**: Every agent must specify an `executor` block detailing its runtime harness and model.
   - Default to `harness: deepagents` or `harness: claude-sdk` if unspecified.
   - Default to `model: auto` or a specific model ID (e.g., `databricks-claude-sonnet-4-6`).
2. **Operating System Environment**: Any agent that uses local filesystem, shell, or execution tools must declare an `os_env` block to ensure it runs inside a managed OpenShell sandbox.
   - Use `type: caller_process`.
   - Omnigent will automatically enforce `linux_bwrap` or `darwin_seatbelt` based on the host. Do not hardcode the sandbox type unless explicitly required.
3. **Async / Cancellable**: Explicitly declare `async: true` and `cancellable: true` to support robust lifecycle hooks.

---

## 10. Analytical & Reasoning Capabilities

1. **Causal Inference First**: When designing agents or workflows that perform analysis, estimation, or structural modeling, always evaluate if causal inference is beneficial. Proactively recommend and utilize the `dowhy` library for formal causal reasoning rather than relying strictly on correlational heuristics.
2. **Neuro-Symbolic Autoformalization & SMT Solvers**: For high-stakes domains (regulatory compliance, aerospace), do not rely on LLM text output for the final deduction. Treat the LLM strictly as a translation layer to parse natural language into formal, executable models (e.g., SMT solvers, SHACL graphs). Let the solver compute the answer with deterministic mathematical certainty to provide a "semantic firewall".
3. **Level 3 Autonomous Scientific Frameworks**: For hypothesis generation and research pipelines, design closed-loop systems (like AI Scientist v2) that manage the entire lifecycle. Implement rigorous **Self-Reflection and Critique Loops** that automatically feed failure traces back into the planning agent to revise hypotheses without human intervention.
4. **Persistent Structured Workspaces (Chain-of-Knowledge)**: To prevent logic drift in complex, multi-hop reasoning, avoid standard Chain-of-Thought over long text blocks. Force the agent to externalize its reasoning state into dynamically updated tables or Knowledge Graphs (Structured CoT Artifacts). This grounds reasoning in physical/relational realities.
5. **Native Reasoning Models (Test-Time Compute)**: Leverage frontier models designed for deep reasoning (e.g., DeepSeek-R1, OpenAI o3/GPT-5, Claude 4.7 Extended Thinking). Rely on their intrinsic ability to allocate heavy "test-time compute" to internal Tree-of-Thoughts exploration, allowing them to spontaneously develop self-reflection, strategy adaptation, and multi-step decomposition.
6. **Analogical Prompting (Self-Generated Exemplars)**: For zero-shot reasoning tasks, the agent's system prompt must instruct it to use Analogical Prompting. Before attempting the target problem, the agent MUST explicitly generate 3-5 relevant problems from varied domains, explain their solutions, and then use those as context to solve the initial problem.
7. **Explicit Structural Mapping**: When performing analogical transfer, agents must not rely on unstructured text. They must explicitly externalize the *relational structure* by generating a structural mapping artifact (e.g., a JSON or YAML graph mapping the Source Domain entities/relations to the Target Domain entities/relations) *before* synthesizing the final answer.
8. **Archetypal Anchoring**: To stabilize complex reasoning in orchestrators, use Archetypal Anchoring. The system prompt must invoke a highly specific, coherent behavioral persona (an "archetype") early in the context window. This anchors the LLM's latent space and drastically reduces hallucinations during deep Tree-of-Thoughts exploration.
9. **Dialectical Synthesis**: Agents tasked with ideation, design, or hypothesis generation must employ Dialectical Reasoning. The agent must explicitly generate a Thesis (proposed solution), an Antithesis (the strongest possible counter-argument or structural flaw), and a Synthesis (a reconciled solution) before delegating or concluding.
10. **Epidemiological Causal Inference (Hill's Criteria)**: Agents evaluating health, scientific, or safety risks must explicitly evaluate associations against Bradford Hill criteria (strength, consistency, temporality, etc.) and map assumed confounders via Directed Acyclic Graphs (DAGs) before drawing conclusions.
11. **Counterfactual Simulation (Do-Calculus)**: When proposing interventions in Predictive Health Maintenance (PHM) or clinical scenarios, the agent must interface with a formal causal engine to simulate `do-interventions` and rank recommendations based on estimated treatment effects, not token probability.
12. **Multi-Model Consensus & Governance**: For high-risk regulatory (GxP) tasks, do not rely on a single model. Employ a Consortium Pattern where a heterogeneous group of models generates candidate reasoning paths, and a distinct Governance Agent evaluates them against safety constraints to synthesize a final auditable decision.
13. **Abductive Root-Cause Isolation**: For diagnostics and system observability, agents must use abductive reasoning—working backward from observed symptoms to find the most plausible explanation using a causal graph, explicitly eliminating hypotheses contradicted by negative evidence.
14. **"Glass Box" Traceability**: In FDA and GxP regulated environments, agents must explicitly document their assumptions, the constraints they are respecting, and their domain boundaries (via an `assumptions_and_constraints` structured output) before executing actions, ensuring full auditability.
15. **Bayesian Belief Updating (Orchestration)**: When orchestrators face high uncertainty (e.g., routing to experts, deciding to retry, or diagnosing complex failures), they must employ Bayes-consistent control layers. The agent explicitly maintains a probabilistic world model (prior beliefs), observes outcomes, and updates routing preferences or diagnostic probabilities (posterior beliefs) systematically.

---

## 11. LangChain-First & DeepAgent-First Architecture

As a LangChain-first company, we strictly prioritize native LangChain, LangGraph, and deepagents ecosystem packages. You MUST NOT use legacy abstractions.

1. **No Legacy AgentExecutor**: Do not use `AgentExecutor` or `initialize_agent`. Use LangGraph (`StateGraph`, `create_agent`) for deterministic control flow.
2. **No Pre-built Chains or Buffers**: Do not use `LLMMathChain`, `SQLDatabaseChain`, or `ConversationBufferMemory`. Rely on LangGraph checkpointers for short-term state, and native Tool Calling.
3. **LangChain v1 Migration Adherence**: 
   - No `langchain-community`. It is deprecated.
   - Use `langchain.agents.create_agent`, NOT `langgraph.prebuilt.create_react_agent`.
   - Use `system_prompt` parameter, NOT the legacy `prompt` parameter.
   - Use LangChain `TypedDict` state schemas.
4. **DeepAgents version >= 0.6.0**: You MUST strictly adhere to the modern deepagents API contract. Legacy properties (e.g., `ls_info`, `ASYNC_GREP_TIMEOUT`) are forbidden. Do not use pre-model or post-model hooks; implement logic via Agent Middleware (`before_model`, `after_model`).

---

## 12. Open-Source First (Observability)

1. **Langfuse is strictly forbidden** to reduce dependency bloat, as we deeply integrate with the native LangChain/LangSmith ecosystem.
2. **LangSmith is the mandated standard** for all tracing, observability, and evaluation. We use local Jaeger/Harbor for open-source self-hosting.

---

## 13. Native Semantic Memory (Store API)

When an agent requires long-term, cross-thread semantic memory (such as retrieving past failures or contextual facts):
1. **No External Vector Databases**: Do NOT configure or instantiate Qdrant, Pinecone, or Chroma.
2. **Native Store Injection**: You MUST rely exclusively on LangGraph's native `BaseStore` API via dependency injection.
3. **InjectedStore Annotation**: Tools that require memory access must use the `store: Annotated[BaseStore, InjectedStore()]` parameter, allowing the orchestrator to dynamically pass the `AsyncPostgresStore` (via `pgvector`) at runtime.
