# WebSocket and SSE Streaming

Long-running multi-agent workflows present a unique observability challenge. Because deterministically routed graphs can execute for several minutes or even hours (especially when waiting on Human-in-the-Loop approvals or massive data ETL operations), synchronous request-response models are insufficient.

The CoReason Workspace Environment exposes **WebSocket** and **Server-Sent Events (SSE)** as first-class interaction surfaces, enabling real-time telemetry and state interaction.

## Authentication

Like the REST API, all WebSocket and SSE endpoints are strictly secured. Clients must initiate connections with the appropriate authentication headers or query parameters (e.g., passing the `API_SECRET_TOKEN` as a bearer token or query string `?token=...` depending on the client library capabilities) to establish a successful connection.

## Real-Time Observability via JSON Patch

Every execution node, internal thought process, tool invocation, and validation error within the LangGraph state machine is broadcast in real-time. 

To optimize payload size and network efficiency, the platform generates real-time telemetry updates. Instead of passing bloated, complete state dictionaries on every graph tick, the platform streams data directly from the **Postgres DB Queue**, ensuring persistent, queryable state.

- **SSE (Server-Sent Events)**: Ideal for uni-directional telemetry, used primarily by headless dashboards or logging aggregators simply looking to monitor a job's progress. Currently, the SSE endpoints (like `/api/v2/agents/{agent_name}/stream`) actively subscribe to Postgres `LISTEN/NOTIFY` channels (e.g. `langgraph_events_{session_id}`) via `asyncpg.add_listener`, yielding true JSON patch events natively from the execution graph.

## Time-Travel Debugging (State Sync)

The WebSocket endpoints stream real-time JSON Patch state updates directly originating from the Postgres checkpointer.

Because the state is streamed synchronously, developers can build live interactive tooling on top of the agent. The primary example of this is the platform's native Time-Travel Debugger, accessible via the `dcode` Text User Interface.

If an agent hallucinates or encounters an execution failure deep within a complex workflow, the WebSocket connection allows a client to transmit a `rewind` command accompanied by a specific `checkpoint_id`. 

The orchestrator will:
1. Halt the current execution graph.
2. Rollback the database state to the exact node matching the `checkpoint_id`.
3. Allow the developer to hot-swap code or modify the payload.
4. Resume execution deterministically from the restored checkpoint.

## Universal Subscription
Following the Multi-Surface Parity mandate, all other platform surfaces (like the Python SDK and MCP Server) inherently rely on and subscribe to these streaming endpoints for their respective real-time consumers.
