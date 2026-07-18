# Chain-of-Symbol (CoS) Reasoning

> **Taxonomy Bucket**: `reasoning/`
> **Scope**: Token-efficient reasoning for spatial, planning, or state-machine tasks.

Traditional Chain-of-Thought (CoT) relies on verbose natural language, which can lead to hallucination in highly structured state-tracking tasks. For planning, workflow execution, and spatial mapping, use **Chain-of-Symbol (CoS)**.

### The CoS Framework
Instruct the agent to use explicit, concise symbols to represent state transitions rather than paragraphs of text.

1. **State Initialization**: Represent the initial state as a symbolic matrix or array.
2. **Transition Tokens**: Use spatial or directional tokens to map progress.
   - Example: `[Task A] -> [Task B] ↑ (Escalation) ↓ (Delegation)`
3. **Verification Checkmarks**: Use strict boolean symbols (`[x]` for complete, `[ ]` for incomplete) to track checklist progression.

### Example System Prompt Injection
*"You must track your progress through the topology. Do not use natural language sentences to describe your state. You MUST use Chain-of-Symbol notation. Maintain a strict `[Current Node] -> [Next Node]` array and mark completed steps with `[x]`."*
