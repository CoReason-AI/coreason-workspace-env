# Anti-Stub Enforcement Policy

The CoReason Workspace Environment operates under a strict **No-Mock, Anti-Stub Policy** (`validation_checklist.md`). 

Because the platform is an opinionated, production-grade DeepAgent factory, faking execution paths, hardcoding success strings, or simulating data connections undermines the fundamental integrity of the generated artifacts.

## The Production Readiness Mandate

To maintain compliance and pass static validation, the following rules apply to all code within the `src/` directory:

1. **Zero Keyword Hits**:
   - The words `mock`, `stub`, `fake`, and `simulate` are completely banned from all execution and orchestration paths.
   - Any commit attempting to bypass actual implementation by using these keywords will fail static analysis.

2. **No Empty Blocks**:
   - Empty `pass` execution blocks inside agent orchestrators are prohibited. Every agent must fulfill a genuine structural role.
   - Project Manager agents (e.g., `frontend_pm`, `agent_pm`) must dynamically compile `LangGraph` StateGraphs with explicit conditional edges, completely eliminating the need for `pass` blocks or mocked `NotImplementedError` stubs.

3. **Genuine LLM Invocation**:
   - Every Maker agent must invoke a real language model using `.with_structured_output()` and strict Pydantic schemas. 
   - Faking generation with a static `"MOCK_SUCCESS"` string is an instant failure.

4. **Authentic Integrations**:
   - The platform relies on real Postgres checkpointers, actual SSE database streams, and local execution vaults.
   - Any component that fakes an API return or bypasses the Kubernetes Vault token checks is strictly prohibited.
