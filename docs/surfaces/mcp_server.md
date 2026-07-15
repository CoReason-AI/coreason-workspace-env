# Headless MCP Server Deployment

The Model Context Protocol (MCP) has rapidly become the universal integration standard across enterprise artificial intelligence applications, functioning effectively as the "USB-C port for AI."

While the vast majority of contemporary agentic frameworks are architected explicitly as **MCP clients** (designed to connect to external servers to consume tools), the CoReason platform differentiates itself through an inversion of control: it is designed from the ground up to be deployed natively as a **headless MCP server**.

## Complex Workflows as Atomic Tools

By deploying as a native MCP server, the entire compiled LangGraph state machine—complete with its Epistemic Firewall and Maker-Checker validation loops—is exposed directly via the protocol standard.

This means that upstream orchestrators, enterprise service buses, or intelligent development environments (IDEs) can dynamically discover and invoke the platform's highly complex, multi-agent workflows as if they were simple, atomic tools.

## Abstracting Topology Complexity

The platform effectively abstracts away the sheer complexity of its internal multi-agent topology. 

An upstream enterprise application simply sends a standardized request to the CoReason server. The platform internally handles:
- Pre-dispatch schema saturation
- Distributed sub-agent delegation
- Mathematical AST and Pydantic validation
- Cryptographic data retrieval

Once the internal Maker-Checker-Approver pipeline successfully resolves, the platform returns the verified, structured output back to the consumer via standard input/output streams (stdio), Server-Sent Events (SSE), or streamable HTTP.

*Technical Note: The MCP Server itself remains stateless; it resolves requests (such as `get_workspace_state`) by dynamically querying the underlying Postgres `langgraph_state` checkpointer. **This integration natively enforces Multi-Tenant State Isolation**, actively filtering queries by `tenant_id` to strictly prevent cross-tenant data leakage. This enables true, secure cross-process state inspection for external IDEs like Cursor.*

## Air-Gapped Interoperability

While some observability platforms offer proprietary SaaS mechanisms to expose agents as servers, the CoReason platform embeds this capability directly into its core infrastructure. This eliminates vendor lock-in to external observability providers and allows for highly secure, air-gapped, on-premise enterprise deployments.
