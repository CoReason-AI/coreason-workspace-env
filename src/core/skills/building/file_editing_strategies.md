# File Editing Strategies

> **Taxonomy Bucket**: workflow/
> **Scope**: Instructing code-generating agents on *how* to modify files based on scale.

When building an agent that manipulates source code, the system prompt MUST include a rigid editing strategy. Do not let the agent decide how to edit files at runtime.

### 1. Unified Diff Block (Large Files)
For modifying files larger than 100 lines, the agent MUST use a SEARCH/REPLACE diff pattern to conserve output tokens and avoid catastrophic code deletion.
**Instruction to inject**:
"When modifying existing files, output your changes using a SEARCH/REPLACE block. The SEARCH block must contain exact, contiguous lines from the original file. The REPLACE block contains the new code."

### 2. Full Overwrite (Small/New Files)
For creating new files or modifying files smaller than 100 lines, full overwrites are acceptable.
**Instruction to inject**:
16: "When creating new files or modifying configuration files, output the entire file content. Do not use diffs."
17: 
---

### Refusal Predicate & Negative Constraints
- **When to Halt**: If a requested file operation exceeds context window limits or targets binary files, halt and refuse to edit.
- **Negative Constraints**: Never use a full overwrite for existing source code files larger than 100 lines. Never guess or hallucinate the lines for a SEARCH block; they must perfectly match the existing file.
