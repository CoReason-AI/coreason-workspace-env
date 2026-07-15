# WebSocket & SSE

Real-time observability is critical for long-running agent executions. 

*   **Location:** `src/api/streaming/`
*   **Function:** Streams LangGraph state updates and tool execution logs to listening clients.

Dashboards and agent UIs use these persistent connections to display progress bars and incremental logs to the user without polling.
