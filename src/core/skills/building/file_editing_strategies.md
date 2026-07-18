# File Editing Strategies

> **Taxonomy Bucket**: workflow/
> **Scope**: Instructing code-generating agents on *how* to modify files based on scale.

When building an agent that manipulates source code, the system prompt MUST include a rigid editing strategy. Do not let the agent decide how to edit files at runtime.



### Integration Contract
- **Compute Constraints**: Stateless
- **Side-Effect Risk**: Read-Only

### 1. Unified Diff Block (Large Files)
For modifying files larger than 100 lines, the agent MUST use a SEARCH/REPLACE diff pattern to conserve output tokens and avoid catastrophic code deletion.
**Instruction to inject**:
"When modifying existing files, output your changes using a SEARCH/REPLACE block. The SEARCH block must contain exact, contiguous lines from the original file. The REPLACE block contains the new code."

### 2. Full Overwrite (Small/New Files)
For creating new files or modifying files smaller than 100 lines, full overwrites are acceptable.
**Instruction to inject**:
"When creating new files or modifying configuration files, output the entire file content. Do not use diffs."


### Output Schema
```json
{
  "action_result": {
    "status": "success",
    "details": "string"
  }
}
```


### Refusal Predicate & Negative Constraints
- **When to Halt**: If the required context is missing, immediately halt execution and return a failure state. Do not attempt to guess or hallucinate parameters.
- **Negative Constraints**: You are strictly forbidden from executing operations outside this defined scope.
