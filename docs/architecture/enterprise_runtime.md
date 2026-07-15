# The Enterprise Runtime (Body)

To operate in a production environment, multi-agent systems must overcome significant scaling and security challenges. The CoReason Workspace Environment implements an Enterprise Runtime that natively addresses asynchronous event looping, strict tenant data isolation, and filesystem confinement.

## High-Performance Asynchronous Execution

Agent frameworks executing complex directed acyclic graphs (DAGs) often suffer from thread-blocking bottlenecks. If an agent initiates a long-running sub-agent or LLM inference task synchronously, it freezes the main application thread.

To prevent this, the CoReason `PlatformOrchestrator` implements an entirely non-blocking async execution layer:
- **`AsyncConnectionPool`**: All database interactions, including WORM (Write Once Read Many) checkpoints and vector similarity searches, utilize `psycopg_pool.AsyncConnectionPool`.
- **`AsyncPostgresSaver`**: LangGraph checkpointer persistence happens via asynchronous streaming.
- **Unblocked FastAPI**: Because `execute_graph()` is fully asynchronous (`await graph.ainvoke`), multiple tenants and agents can execute massive cognitive workflows concurrently without blocking the core HTTP/WebSocket router loops.

## True Multi-Tenant Data Isolation

Unlike simplistic multi-agent sandboxes, this platform is designed to host multiple isolated workspaces on a shared infrastructure. 

- **Schema-per-Tenant:** Instead of co-mingling LangGraph checkpoint threads into the `public` schema, the runtime dynamically isolates each project. When the orchestrator executes, it forces the connection `search_path` to map explicitly to a dedicated schema (e.g., `project_019f67e0_6199_7b94_8beb_82eccdadc3eb`).
- **Safe State Backups:** Because checkpointer tables are isolated by schema, the `export_project` capability uses `pg_dump -n <schema>` to perfectly extract only the relevant workspace memory without leaking adjacent tenant data. Similarly, project imports drop and restore only the isolated schema.

## Physical Sandboxing and Path Security

Generative AI agents must be confined. A compromised agent (e.g., via prompt injection) could attempt to read or overwrite system-critical files across the host OS.

The runtime integrates `validate_safe_path` directly into the IO gateways:
- All dynamic file generation (such as MkDocs workspace scaffolding) forces strict base-directory pinning.
- Any attempt by an agent or user to specify paths outside the designated `WORKSPACE_ROOT / "projects"` directory results in a severe validation failure and halts execution. 
- API endpoints that operate on files securely traverse and validate paths, blocking all traversal payloads (`../` or `C:\Windows`).
