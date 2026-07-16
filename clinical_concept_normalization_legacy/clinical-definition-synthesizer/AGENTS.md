# AGENTS.md - Environment & Integration Rules
 
## Platform Bounds
1. **Sandboxing**: You operate in a zero-trust, isolated container environment.
2. **Access Control**: You do not have internet access, database query permissions, or external API tools.
3. **Authorized Tool Routing**: You only have access to:
   * `sequentialthinking` for local reasoning scratchpad.
4. **State Sharing**: The output must conform strictly to the Pydantic schema defined in `SKILL.md` to be parsed and saved to the global LangGraph workflow state.