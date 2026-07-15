# The DeepAgent Pattern

The CoReason platform is built upon the **DeepAgent** pattern using LangGraph. This architecture mandates that agents are strictly defined via declarative configurations rather than imperative code, ensuring high portability, determinism, and safety across the swarm.

## 1. YAML as the Single Source of Truth

Agents are not instantiated via massive, dynamic Python scripts stringing together prompts. Instead, every agent is strictly defined via a `pyagentspec`-compatible `agent.yaml` manifest.

*   **The Blueprint:** The YAML file defines the agent's core persona, system boundaries, LLM configurations, and the specific tools (Skills) it has access to.
*   **Decoupled Logic:** This prevents developers from dynamically injecting unstable state or massive logic loops into the agent's system prompt at runtime. The YAML acts as a rigid, auditable contract.

## 2. Namespace and Taxonomy Consistency

The routing topology of the platform relies on strict naming invariants:
*   The `name` field in every `agent.yaml` **MUST exactly match** the `snake_case` name of the folder it resides in.
*   For example, an agent located at `src/agents/project_initiation/` must have `name: project_initiation` in its YAML manifest. 
*   This strictly ensures that the internal Agent ID perfectly matches the namespace and filesystem routing logic for dynamic loading.

## 3. Progressive Disclosure (Skills-Based Architecture)

To prevent the LLM's context window from collapsing under the weight of complex instructions, we utilize **Progressive Disclosure**:

*   **No Hardcoded Knowledge:** Complex workflow logic, domain expertise, or dense formatting instructions must **NEVER** be hardcoded into the agent's core system prompt inside the YAML.
*   **Atomic Skills:** Instead, encapsulate complex operations into strictly-typed, atomic Python functions adorned with `@tool` (Skills).
*   **Just-in-Time Context:** The LLM is provided only with the tool signatures (the "menu" of capabilities). If the LLM encounters a problem it needs to solve, it calls the specific tool, and only then is the complex logic or deep domain knowledge executed deterministically in Python. 

By pushing complexity out of the stochastic prompt and into deterministic Python tools, the DeepAgent pattern maintains a lean, focused, and highly reliable reasoning loop.