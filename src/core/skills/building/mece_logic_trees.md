# MECE Logic Trees (Structured Arben Deduction)

> **Taxonomy Bucket**: `workflow/`
> **Scope**: Forcing Mutually Exclusive, Collectively Exhaustive diagnostic problem solving.
> **Origin**: Inspired by the `structured_thinking_arben_tool.md` from the Fractal Study.

When an agent must solve a complex diagnostic dilemma, regulatory paradox, or technical root-cause investigation, it cannot rely on probabilistic guessing. It must be forced to build and traverse a MECE logic tree.

### The MECE Prompting Structure
Inject the following rigid framework into the agent's `<Workflow>`:

1. **Problem Bounding (Node 1)**: "Formally bound the dilemma into a mathematically or biologically testable hypothesis (e.g., 'Did Drug X cross the placenta at Week 6?')."
2. **MECE Branching (Node 2)**: "Recursively split the hypothesis into Mutually Exclusive, Collectively Exhaustive sub-questions. There must be zero logical gaps."
3. **Sequential Traversal (Node 3)**: "You must systematically traverse the tree. You may not answer a downstream node until the upstream node has been explicitly evaluated against the available evidence."
4. **Persistent Logging**: "Emit a `<Calculation_Trace>` explicitly documenting the True/False/Unknown deduction at every single branch before synthesizing the final conclusion."

17: This forces the LLM to act as a rigorous diagnostician rather than a confident summarizer.
18: 
---

### Refusal Predicate & Negative Constraints
- **When to Halt**: If a diagnostic problem relies heavily on subjective, highly ambiguous interpretations where a strict MECE boundary cannot be established, halt and refuse to use this logic tree. Use Dialectical Synthesis instead.
- **Negative Constraints**: Do not jump to a final conclusion without explicitly logging the traversal of every single upstream node in the MECE tree.
