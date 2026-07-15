# MCP Server Surface

The Model Context Protocol (MCP) server is the primary way that upstream AI agents and IDEs interact with the CoReason Workspace.

## Native Identity

Because this platform builds systems that are *deployable as MCPs*, the platform itself must be consumable as an MCP server. Every agent operation, project initiation, and database query is exposed as an MCP tool.

*   **Location:** `src/mcp/`
*   **Transport:** JSON-RPC over stdio or SSE.

## Schema Consistency

The MCP server exposes the exact same schemas as the CLI and REST API. For example, `mcp_write_vectors` accepts the same Pydantic payloads as the corresponding REST endpoint.
