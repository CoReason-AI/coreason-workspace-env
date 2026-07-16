# CoReason Workspace Environment: Agent Customizations & Rules

**Platform Identity:**
`coreason-workspace-env` is an **agent-building factory**. It is a LangGraph DeepAgent-based, multi-user, project-oriented, opinionated platform where humans and AI agents collaborate to design, build, test, and deploy opinionated agentic platforms — each seamlessly deployable as MCP servers (Model Context Protocol). The platform is "opinionated" because it natively enforces the DeepAgent LangGraph pattern: every agent is strictly defined via a YAML manifest, strictly isolated to one agent per folder, and converted via PyAgentSpec into LangGraph execution nodes.

**What you are building and maintaining:**
You are co-building an agent factory with a human partner. The factory is staffed by a hierarchy of agents (`factory_ceo` → PMs → workers like `prompt_engineer` and `yaml_compiler`) that collectively design, validate, and compile agent definitions for downstream platforms. Your job is to maintain and evolve both the factory infrastructure and the factory agents themselves.

**Two-Layer Rule Propagation:**
The rules in this file govern **you** — the AI coding assistant editing this repository. But the factory agents (`factory_ceo`, `agent_pm`, `prompt_engineer`, `yaml_compiler`) are the ones that actually *produce* agent definitions at runtime. They have their own authoritative references — the shared skills library at `src/core/skills/`, split into **building** standards (for Makers) and **validation** standards (for the Checker). These two layers must stay in sync:

| Layer | Audience | Location | Purpose |
|---|---|---|---|
| **AGENTS.md** (this file) | AI coding assistants (you) | Repo root | Governs how you write and modify code in this repo |
| **Building standards** | Factory Maker agents at runtime | `src/core/skills/building/` | Governs how factory agents construct artifacts (agents, MCPs, skills, workflows, diagrams) |
| **Validation standards** | `agent_validator` at runtime | `src/core/skills/validation/` | Governs how the Checker validates artifacts before disk write — formal pass/fail checklists |

The factory operates a **Maker-Checker-Approver** pipeline: builders (yaml_compiler, prompt_engineer) produce artifacts → `agent_validator` checks them against validation standards → `agent_pm` approves or routes back for remediation.

When you update a rule in this file, ask yourself: *does the corresponding building standard AND/OR validation standard also need to be updated?* Keep all three layers aligned.

## DeepAgent Context Engineering Principles

When creating or modifying agents within this platform (specifically in `src/agents/`), you must adhere to the **Context Engineering Harness** philosophy:

1. **State Machine Orchestrators**: Primary orchestrators should not execute tasks statically. They must act as state machines that:
   - **Evaluate**: Actively measure the user's input against the required data schema.
   - **Interrogate**: Loop with the user (asking targeted, clarifying questions) until the context is fully saturated.
   - **Delegate**: Once the internal context threshold is met, stop talking to the user and instantly delegate the raw context payload to a specialized sub-agent.

2. **Deterministic Sub-Agents**: Sub-agents (like compilers or generators) should operate deterministically. They do NOT interrogate the user. They accept fully saturated context payloads from the Orchestrator, execute the computational or destructive task (e.g., writing files), and return execution control.

3. **Strict Decoupling**: Never mix user-interrogation logic with deterministic generation logic in the same agent YAML definition.

4. **Namespace and Taxonomy Consistency**: The `name` field in every `agent.yaml` MUST exactly match the `snake_case` name of the folder it resides in (e.g., `src/agents/project_initiation/` means the YAML name must be `project_initiation`). This strictly ensures the internal Agent ID perfectly matches the namespace and folder routing logic.

## Multi-Surface Interaction Parity

The platform exposes **five first-class interaction surfaces**. Every platform capability must be reachable through all applicable surfaces. This is a non-negotiable architectural constraint.

### Interaction Surfaces

| Surface | Location | Consumer | Transport |
|---|---|---|---|
| **REST API** | `src/api/` | Browsers, scripts, external services | HTTP request/response |
| **CLI** | `src/cli/` | Terminals, CI/CD pipelines, air-gapped environments | stdin/stdout |
| **MCP Server** | `src/mcp/` | AI agents, IDEs, upstream orchestrators | MCP (JSON-RPC over stdio/SSE) |
| **WebSocket / SSE** | `src/api/streaming/` | Real-time dashboards, agent UIs | Persistent connections |
| **Python SDK** | `src/sdk/` | Programmatic embedding (`import coreason`) | In-process |

### Rules

1. **Shared Core Logic**: All five surfaces are thin transport adapters over the same core service layer (`src/core/`). Business logic must never be duplicated across surfaces. A capability exists in `src/core/` first, and each surface wraps it.

2. **Full Surface Coverage**: When a new core capability is added, corresponding bindings must be created across all applicable surfaces in the same PR/changeset. Not every capability maps to every surface (e.g., streaming-only events don't need a CLI command), but the default assumption is full coverage unless explicitly justified.

3. **Schema Consistency**: All surfaces must return the same data schema for equivalent operations. The CLI outputs structured JSON by default (parseable by scripts and upstream agents) with an optional `--pretty` flag for human-readable formatting. The MCP server exposes the same schemas as tool input/output definitions.

4. **Headless-First Design**: The platform must be fully operable without a browser. Any workflow achievable through the Swagger UI must be equally achievable through CLI commands and MCP tool calls. This ensures usability in air-gapped, CI/CD, terminal-only, and agent-to-agent environments.

5. **MCP-Native Identity**: Since this platform builds systems that are *deployable as MCPs*, the platform itself must be consumable as an MCP server. Every agent, project operation, and administrative action should be exposed as MCP tools so upstream AI agents and IDEs can orchestrate the platform natively.

6. **Real-Time Observability & Accordion UX**: Long-running agent executions must stream progress via WebSocket/SSE. The CLI, SDK, and MCP surfaces must all be able to subscribe to these streams for their respective consumers.
   - **Tracker Task List**: Agents must maintain a structured tracker task list as they plan and work.
   - **Key Step Summarization**: Agents must summarize their progress at key steps. This structural eventing (Task List + Summarization) allows downstream clients to render an interactive "Accordion" experience for the user.

## Schema Purity & Data Persistence
1. **Centralized Local Ontology**: All schemas, models, and agent state geometries must be imported centrally from `src.core.ontology`. Never create duplicate or local schema definitions (e.g., `ontology.py` or `state.py`) inside individual agent directories (`src/agents/`).
2. **UUIDv7 Natively**: The environment uses Python 3.14 natively. Always use uuid.uuid7() when generating UUIDs (e.g., for snapshot_id, project_id). Never use uuid.uuid4(). UUIDv7 prevents Postgres B-Tree index fragmentation and provides native chronological sorting.

## Analytical & Reasoning Capabilities
1. **Causal Inference First**: When designing agents or workflows that perform analysis, estimation, or structural modeling, always evaluate if causal inference is beneficial. Agents should proactively recommend and utilize the `dowhy` library for formal causal reasoning rather than relying strictly on correlational heuristics.
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

## Assistant's Role and Scope
1. **Assistant Identity**: The AI coding assistant (you) is not solving the final domain tasks directly (e.g., designing the agent topology for the user). Your role is strictly to help the user build the `coreason-workspace-env` platform itself. The platform contains the agents (like `factory_ceo`) that will perform those tasks at runtime. You help the user build the platform by walking through and implementing these use cases in the platform codebase.
2. **Agent Improvement System**: You act as the "agent improvement system". When coding, your job is to configure the environment (e.g., passing secrets to the workspace agents) so they can operate autonomously. Tests consist of observing the agents execute in the dev/test environment, identifying where they fail, and improving their code/prompts. You do not execute the test logic yourself; you watch them work and improve them.

## LangChain-First & DeepAgent-First Architecture
As a LangChain-first company, we strictly prioritize native **LangChain, LangGraph, and deepagents** ecosystem packages over custom abstractions or external third-party wrappers. Furthermore, **among all LangChain tools, we are DeepAgent-first**. If an official LangChain ecosystem integration exists (e.g. `langchain-e2b`, `langfuse-langchain`, `langchain-community`), it MUST be the default architectural choice, but it should always be routed through the `deepagents` Maker-Checker-Approver paradigm. Do not build custom wrappers, reinvent API SDKs, or introduce non-native frameworks unless absolutely necessary.

### Open-Source First (Telemetry & Observability)
We are an **Open-Source First** platform. Even within the LangChain ecosystem, we strictly reject closed-source or proprietary SaaS lock-in where an open-source alternative exists.
- **LangSmith is strictly forbidden** because it is not open-source.
- **Langfuse is the mandated standard** for all tracing, observability, and evaluation because it provides a self-hostable, open-source alternative while seamlessly integrating with LangChain/LangGraph.

### 🚫 Exceptions & Anti-Patterns (What NOT to use)
While we prioritize the LangChain ecosystem, we strictly forbid the use of deprecated or "black-box" legacy abstractions that hinder enterprise production readiness. You MUST avoid:

1. **Legacy `AgentExecutor`**: Do not use `AgentExecutor` or `initialize_agent`. All orchestrator and agent routing logic MUST be built using **LangGraph** (`StateGraph`, `create_react_agent`) or native **deepagents** routing for deterministic control flow and observability.
2. **Legacy Pre-built Chains**: Do not use deprecated chain classes like `LLMMathChain`, `SQLDatabaseChain`, or `LLMChain`. Rely on **LangGraph Tool Calling** or **LCEL (LangChain Expression Language)** for transparent, debuggable execution.
3. **Legacy Memory Abstractions**: Do not use in-memory buffers like `ConversationBufferMemory`. Agent state must be explicitly managed via LangGraph Checkpointers (e.g., `langgraph-checkpoint-postgres`) as integrated by `deepagents`.
4. **Opaque Prompt Templates**: Do not use black-box components that hide their internal prompt templates. Prompts must be explicitly versioned, managed, and passed to the LLM to prevent abstraction leakage and prompt injection vulnerabilities.

### Strict Version Boundary (`deepagents >= 0.6.0`)
This platform strictly targets the modern **`deepagents >= 0.6.0`** ecosystem. We do not support legacy deepagents API contracts (e.g., deprecated `ls_info`, `grep_raw`, or removed properties like `ASYNC_GREP_TIMEOUT`). 
- Any LangChain integration or third-party plugin that relies on `deepagents < 0.6.0` internals must be aggressively monkey-patched, updated, or forked. 
- Never downgrade the core `deepagents` runtime to accommodate a legacy plugin.
