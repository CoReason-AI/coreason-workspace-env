# Prompt Complexity Bounds

> **Scope**: Identifying when a prompt is too complex and must be transitioned to an agentic workflow.

When writing or compiling agent prompts, evaluate them against these boundary conditions. If any condition is met, the single-prompt design is invalid and MUST be decomposed.

### 1. The Partial Completion Threshold
If a prompt contains more than 3 distinct procedural steps (e.g., "1. Extract X, 2. Validate Y, 3. Generate Z"), it crosses the Partial Completion Threshold. LLMs routinely skip steps in monolithic prompts as complexity scales linearly. 
**Action**: Split the prompt into sequential agentic tasks linked by a strict state graph.

### 2. Cognitive Function Mixing
An LLM performs poorly when forced to rapidly switch contexts or cognitive modes (e.g., oscillating between creative generation and rigid validation).
**Rule**: Do not mix Extraction, Classification, Validation, and Generation in a single prompt.
**Action**: Isolate each cognitive function into a distinct Sub-Agent worker prompt (Single Responsibility Principle).

### 3. Cascading Error Brittleness
If adjusting one instruction in a prompt reliably breaks the output of another unrelated instruction within the same prompt, the prompt is too brittle.
**Action**: Decompose the workflow. Adding a new task to a workflow graph is a linear complexity increase (`O(n)`), whereas adding instructions to a monolithic prompt scales complexity exponentially.
