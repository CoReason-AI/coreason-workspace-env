# WebSocket and SSE Streaming

Long-running multi-agent workflows present a unique observability challenge. Because deterministically routed graphs can execute for several minutes or even hours (especially when waiting on Human-in-the-Loop approvals or massive data ETL operations), synchronous request-response models are insufficient.

The CoReason Workspace Environment exposes **WebSocket** and **Server-Sent Events (SSE)** as first-class interaction surfaces, enabling real-time telemetry and state interaction.

## Real-Time Observability

Every execution node, internal thought process, tool invocation, and validation error within the LangGraph state machine is broadcast in real-time. 

- **SSE (Server-Sent Events)**: Ideal for uni-directional telemetry, used primarily by headless dashboards or logging aggregators simply looking to monitor a job's progress.
- **WebSockets**: A full-duplex bi-directional channel enabling interaction with the live state stream.

## Time-Travel Debugging (State Sync)

The `src/api/streaming/state_sync.py` WebSocket endpoint streams real-time LangGraph state updates directly from the Postgres checkpointer.

Because the state is streamed synchronously, developers can build live interactive tooling on top of the agent. The primary example of this is the platform's native Time-Travel Debugger.

If an agent hallucinates or encounters an execution failure deep within a complex workflow, the WebSocket connection allows a client (such as the CoReason CLI) to transmit a `rewind` command accompanied by a specific `checkpoint_id`. 

The orchestrator will:
1. Halt the current execution graph.
2. Rollback the database state to the exact node matching the `checkpoint_id`.
3. Allow the developer to hot-swap code or modify the payload.
4. Resume execution deterministically from the restored checkpoint.

## Universal Subscription
Following the Multi-Surface Parity mandate, all other platform surfaces (CLI, Python SDK, MCP Server) inherently rely on and subscribe to these streaming endpoints for their respective real-time consumers.
