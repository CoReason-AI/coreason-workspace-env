# Prompt Compression Techniques

> **Taxonomy Bucket**: workflow/
> **Scope**: Optimizing token efficiency for agent-to-agent communication.

When writing internal prompts (prompts used by Orchestrators to speak to Sub-Agents), use agent-side prompt compression to save tokens.



### Integration Contract
- **Compute Constraints**: Stateless
- **Side-Effect Risk**: Read-Only

### Caveman Prompting
Agent-to-agent communication does not need to be grammatically correct or polite. It only needs to carry maximum semantic density.

1. **Remove Politeness**: Never use "Please", "I need you to", or "Could you".
2. **Remove Articles/Stop Words**: Strip "the", "a", "an". 
3. **Use Symbolic Shorthand**: Use logical operators (`->`, `&&`, `!`) instead of long sentences.

**Example of Bad Meta-Prompt**:
"Please analyze the following log file and tell me if you find any errors related to the database connection."

**Example of Compressed Meta-Prompt**:
"TASK: analyze_logs. TARGET: database_connection. RETURN: Error[] || None."


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
