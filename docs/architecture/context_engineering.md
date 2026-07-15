# Context Engineering Harness

The CoReason platform strictly adheres to the **Context Engineering Harness** philosophy when designing multi-agent systems. This architectural pattern fundamentally separates the *acquisition* of information from the *execution* of tasks.

Traditional LLM applications often blend chatting and doing, leading to unpredictable failure states where an agent attempts a kinetic action (like writing a file or querying a database) before it fully understands the user's intent. The Context Engineering Harness prevents this through strict decoupling.

## The Three Pillars of Context Engineering

### 1. State Machine Orchestrators (The "Front Desk")
Primary orchestrators are the only agents permitted to interact with the human user. They act as rigid state machines, not open-ended conversationalists. Their sole purpose is to populate a specific Pydantic data schema. 

They execute a continuous loop of:
*   **Evaluate**: Actively measure the current state of the conversation against the required Pydantic data schema. What fields are missing? What constraints are violated?
*   **Interrogate**: Ask the user highly targeted, clarifying questions to fill the missing gaps. 
*   **Delegate**: The moment the internal context threshold is met (the Pydantic model is fully valid), the orchestrator *stops talking* to the user and instantly delegates the saturated context payload to a downstream sub-agent.

### 2. Deterministic Sub-Agents (The "Factory Floor")
Sub-agents are the workers. They are mathematically forbidden from interrogating the user. 
*   They accept a fully saturated, validated context payload from the Orchestrator.
*   They execute the computational, generative, or destructive task (e.g., compiling code, modifying the database, fetching external APIs).
*   They return execution control (and the final state payload) back to the Orchestrator.

### 3. Strict Decoupling
Never mix user-interrogation logic with deterministic generation logic in the same agent YAML definition. 
*   If an agent has a tool that modifies the filesystem, it should not have a system prompt telling it to "chat nicely with the user."
*   If an agent is designed to interview the user, it should not have access to kinetic execution tools.

## Why This Matters

By forcing this separation, we guarantee that expensive or destructive operations only occur when the system has mathematically proven (via Pydantic validation) that it possesses the exact parameters required to succeed. It transforms the stochastic nature of LLMs into a deterministic pipeline.