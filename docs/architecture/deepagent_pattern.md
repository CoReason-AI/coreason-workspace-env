# The DeepAgent Pattern

The CoReason Workspace Environment implements an opinionated variant of the DeepAgent pattern. While the industry frequently treats multi-agent systems as experimental scripts, this platform enforces a strict Infrastructure as Code (IaC) approach, leveraging deterministic mathematical boundaries rather than heuristic prompting.

## Declarative Agent Manifests (IaC)

Agents within the platform are not instantiated via complex, hardcoded Python boilerplate. Instead, they are defined via strictly typed, `pyagentspec`-compatible **YAML manifests**. 

This shift to declarative infrastructure treats agent definitions as portable, version-controlled configurations. Platform engineers, data scientists, and domain experts define the persona, objectives, boundaries, and tool access of an agent entirely within YAML, abstracting away the underlying graph compilation logic.

## Dynamic LangGraph Compilation

The platform acts as a headless agent factory. At runtime, a specialized YAML compiler reads the agent manifest and dynamically synthesizes an executable **LangGraph StateGraph** node.

This methodology enforces deterministic routing:
- It eliminates the vulnerability of *deliberation cascades*, where probabilistic LLMs loop aimlessly trying to determine the next workflow step.
- Every transition between cognitive agents, functional tools, and human-in-the-loop validation gates is bound by defined structural edges and programmatic conditional routing logic.

## Progressive Disclosure

A primitive practice in early AI engineering was to load massive system prompts containing all possible instructions and tools into an agent's context window at instantiation. This frequently leads to catastrophic forgetting and context collapse.

By utilizing dynamic YAML-to-LangGraph compilation, the CoReason platform natively enforces **Progressive Disclosure**:
- The YAML manifest dictates exactly *which* skills, memory segments, and tools are injected into the context window at *specific* nodes in the graph.
- Agents are only provided the tools and context they need for their immediate mathematical or functional objective, keeping context windows pristine and highly token-efficient.

## Project-Oriented Isolation

As an agent-building factory, the platform strictly isolates one agent per folder (`src/agents/<agent_name>`). The `name` field in every `agent.yaml` MUST exactly match the `snake_case` name of the folder it resides in. This namespace and taxonomy consistency mathematically ensures that internal routing IDs perfectly match the filesystem routing logic.

## Structural Eventing: Trackers & Accordion UX

To prevent cognitive overload from raw streaming log spew, the platform strictly enforces structural eventing inside agent workflows:
- **Tracker Task Lists**: Agents are mandated to maintain and stream structured TODO checklists outlining their planned and completed tasks.
- **Accordion Summaries**: Agents summarize their progress at key execution steps, providing human-readable checkpoint digests.

This structural data is broadcast seamlessly over JSON Patch state streams, allowing downstream clients (like the `dcode` DeepAgents Code TUI) to render polished **Accordion UX** interfaces. Users can monitor macro-level progress via task summaries and expand accordions only when they need to drill down into raw LLM telemetry.