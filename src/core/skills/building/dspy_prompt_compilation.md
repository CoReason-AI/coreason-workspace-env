# DSPy Prompt Compilation Pattern

> **Taxonomy Bucket**: workflow/
> **Scope**: Moving from manual prompt engineering to programmatic prompt compilation.

When constructing complex agents that process varying payloads, do not rely solely on static hand-written system prompts. Instead, implement the DSPy 3.0 Prompt Compilation pattern where possible.

### The Compilation Workflow

1. **Define the Signature**: Explicitly define the input and output variables, not the instructions.
   - Example: `Input(schema="User Request") -> Output(schema="JSON Tracker Task List")`
2. **Provide Exemplars (Few-Shot)**: Supply 5-10 high-quality examples of correct Input->Output pairs.
3. **Compile via Teacher Model**: Use a frontier reasoning model (e.g., DeepSeek-R1 or GPT-5) as the "Teleprompter" or "Optimizer" to automatically generate the optimal system prompt based on the Signature and Exemplars.
4. **Deploy to Student Model**: Deploy the compiled prompt to a faster, cheaper production model (e.g., GPT-4o-mini, Claude 3.5 Haiku).

16: By treating prompts as compiled code, you decouple the *intent* (Signature) from the *implementation* (the exact words in the prompt).
17: 
---

### Refusal Predicate & Negative Constraints
- **When to Halt**: If the task relies on zero-shot reasoning where a dataset of 5-10 high-quality Input/Output exemplars cannot be defined, halt and refuse to use DSPy compilation. Fall back to structured meta-prompting.
- **Negative Constraints**: Do not attempt to hand-write or manually engineer the final prompt for the student model; force the reasoning model to compile it.
