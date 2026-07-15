# The Brain / Body Dichotomy

The CoReason Workspace Environment physically enforces a strict architectural boundary between **Intent** and **Execution**. This is achieved by separating the repository into two primary domains: The Brain and The Body.

## The Brain (`src/agents/`)

The Brain represents pure cognitive intent. It defines *what* the system should do, what persona it embodies, and what logic dictates its decisions.

**Crucially, the Brain contains zero infrastructure code.**

Inside an agent's directory (e.g., `src/agents/factory_ceo/`), you will find:
- **`agent.yaml`**: The universal declarative manifest defining the agent's identity, required dependencies, and skill registry.
- **System Prompts**: The core persona definitions and mathematical boundaries given to the LLM.
- **Domain Logic**: The pure Python functions representing functional sub-routines (e.g., context saturation checks).
- **`StateGraph` Definitions**: The LangGraph nodes and edges that define the agent's deterministic cognitive routing.

The Brain does not know about Kubernetes, FastAPI, Postgres pooling, or WebSockets. It is a completely portable, air-gapped unit of logic.

## The Body (`src/core/`)

The Body is the universal runtime harness. It is an enterprise-grade execution engine that mounts the Brain and wires it into the physical world.

The Body contains:
- **`PlatformOrchestrator`**: Located in `src/core/engine/deepagent_runtime.py`, this is the swappable DeepAgent harness that dynamically reads the `agent.yaml`, mounts the LangGraph `StateGraph`, and executes it.
- **Enterprise Persistence**: Handles WORM (Write Once Read Many) storage and Postgres connection pooling (`AsyncConnectionPool`).
- **Interaction Surfaces**: The REST API, CLI, WebSocket, and MCP Server layers that expose the mounted Brain to users and external services.

By enforcing this strict dichotomy, the CoReason platform achieves a "Swappable Harness" model. A Brain exported from this platform can be seamlessly mounted into any compatible Body (such as an embedded mobile runtime or a massive distributed cloud orchestrator) without rewriting a single line of logic.
