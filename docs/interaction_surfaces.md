# Interaction Surfaces

The CoReason Workspace Environment exposes five distinct interaction surfaces. Following the platform's **Multi-Surface Parity** mandate, none of these surfaces implement business logic. They operate exclusively as thin transport adapters delegating to `src.core.services`, ensuring that operations behave identically and return the same data structures regardless of how they are invoked.

## 1. REST API
The platform exposes a comprehensive **FastAPI-powered REST API**.
- **Pydantic Schema Purity**: All API payloads and responses are strictly governed by the centralized `src.core.ontology` module. The router relies on strict Pydantic definitions to mathematically reject malformed payloads before execution.
- **Security & Tenant Isolation**: The API uses Bearer Token authentication. When authenticated, the user's `tenant_id` ensures isolated Postgres querying.
- **UUIDv7**: Utilizes UUIDv7 natively for all database primary keys to prevent index fragmentation and provide native chronological sorting.

## 2. Command Line Interface (CLI)
The fully-featured headless CLI is built using **Typer** and maps user arguments to asynchronous background execution services via `asyncio.run()`.
- **Core Operations**: Creating projects, triggering agent builds, managing OCI registry operations (push/pull), and air-gapped export/import.
- **Context Engineering Enforcement**: CLI commands are evaluated by the State Machine Orchestrator for schema saturation. Vague inputs will prompt for clarification.

## 3. Model Context Protocol (MCP) Server
Since the platform is an agent-building factory, it natively exposes itself as a **Model Context Protocol (MCP)** server via `FastMCP`.
- Upstream IDEs and agents can invoke the exact same core capabilities (e.g., `build_agent_platform`, `export_oci_bundle`) using JSON-RPC over `stdio` and `SSE`.
- Tools are grouped logically: Causal Server Tools, Memory Server Tools, and Project Tools.

## 4. WebSocket & Server-Sent Events (SSE)
Real-time streaming is heavily leveraged to provide interactive observability into the long-running agent execution processes, powering the UI's Accordion UX.
- **`crdt` (Collaborative Editing)**: Real-time Operational Transformation events for artifact editing.
- **`tty` (Terminal Passthrough)**: Raw bidirectional pipe streaming stdout/stderr from Docker containers.
- **`state_sync`**: Streams immutable snapshot updates emitted by the LangGraph Postgres Checkpointer.
- **`agent_progress`**: Streams structural eventing messages and task lists.

## 5. Python SDK
The pure-Python SDK (`import coreason`) provides programmatic embedding for external Python scripts, orchestrators, or DAGs.
- It is an HTTP wrapper over the REST API via the `httpx` library.
- Automatically handles Authentication, Pydantic model formatting, and asynchronous HTTP dispatch.
- **Usage**: Requires `asyncio`. Methods must be `await`ed.
