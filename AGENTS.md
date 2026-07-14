# CoReason Workspace Environment: Agent Customizations & Rules

**Platform Definition:**
`coreason-workspace-env` is a LangGraph DeepAgent-based, multi-user, project-oriented, opinionated agent-building platform. It enables multiple humans and agents to collaborate together to build opinionated agentic platforms that are seamlessly deployable as MCPs (Model Context Protocol servers). The platform is "opinionated" because it natively enforces the DeepAgent LangGraph pattern: every agent is strictly defined via a YAML manifest, strictly isolated to one agent per folder, and converted via PyAgentSpec into LangGraph execution nodes. The platform ships with a native suite of administrative agents (like the `project_initiation` supervisor) to assist humans in bootstrapping and creating these downstream opinionated agentic platforms.

## DeepAgent Context Engineering Principles

When creating or modifying agents within this platform (specifically in `src/agents/`), you must adhere to the **Context Engineering Harness** philosophy:

1. **State Machine Orchestrators**: Primary orchestrators should not execute tasks statically. They must act as state machines that:
   - **Evaluate**: Actively measure the user's input against the required data schema.
   - **Interrogate**: Loop with the user (asking targeted, clarifying questions) until the context is fully saturated.
   - **Delegate**: Once the internal context threshold is met, stop talking to the user and instantly delegate the raw context payload to a specialized sub-agent.

2. **Deterministic Sub-Agents**: Sub-agents (like compilers or generators) should operate deterministically. They do NOT interrogate the user. They accept fully saturated context payloads from the Orchestrator, execute the computational or destructive task (e.g., writing files), and return execution control.

3. **Strict Decoupling**: Never mix user-interrogation logic with deterministic generation logic in the same agent YAML definition.

4. **Namespace and Taxonomy Consistency**: The `name` field in every `agent.yaml` MUST exactly match the `snake_case` name of the folder it resides in (e.g., `src/agents/project_initiation/` means the YAML name must be `project_initiation`). This strictly ensures the internal Agent ID perfectly matches the namespace and folder routing logic.
