# Conversational Routing (GroupChat)

> **Taxonomy Bucket**: workflow/
> **Scope**: Designing dynamic A2A (Agent-to-Agent) conversational graphs (AutoGen topology).

When the user requests a multi-agent system where agents need to share tools, argue, or deliberate in real-time, Builders must use the Conversational Routing topology.

### The GroupChat Topology
1. **The Chat Manager**: Instead of hardcoding execution paths, create a `GroupChatManager` agent. Its sole responsibility is to read the conversational transcript and decide "Who should speak next?" based on the current context.
2. **Shared Tool Execution**: Unlike crews where tools are siloed, conversational agents can propose a tool call in the chat, and a specialized `ExecutorAgent` runs the code and pastes the result back into the shared transcript.
3. **Termination Conditions**: The Chat Manager must have strict termination heuristics (e.g., "If the word 'APPROVED' is spoken by the QA agent, halt the conversation and return the final summary to the user").

**Prompting Rule**:
14: The `GroupChatManager` prompt must be purely algorithmic: `"Read the last 5 messages. Based on the rules below, output ONLY the name of the next agent who should respond: [Agent_A, Agent_B, ExecutorAgent]."`

---

### Refusal Predicate & Negative Constraints
- **When to Halt**: If the workflow requires strict, sequential determinism with no room for debate, halt and refuse to use the GroupChat topology. Use a Plan-and-Execute pipeline instead.
- **Negative Constraints**: The Chat Manager must never execute tools or generate final artifacts itself; its sole responsibility is routing execution control to the next agent.
