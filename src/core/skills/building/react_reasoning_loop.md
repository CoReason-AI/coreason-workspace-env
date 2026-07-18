# ReAct Reasoning Loop (Reason + Act)

> **Taxonomy Bucket**: `workflow/`
> **Scope**: Grounding agent logic in physical or external reality via tools.

When building an agent that has access to external tools (APIs, CLIs, databases), it must not blindly execute commands. It must be explicitly prompted to use the ReAct (Reason + Act) loop.

### The ReAct Prompting Structure
Inject the following strict requirement into the agent's `<Constraints>` and `<OutputFormat>`:

**Rule**: "You may not execute any tool or action without first explicitly writing out your reasoning."

**Format**:
```text
Thought: [Explain your current understanding of the state and why you need to take an action]
Action: [The explicit tool call]
Observation: [The result returned by the environment]
```

This ensures the agent grounds its logic in actual observations rather than hallucinating the result of the action.
