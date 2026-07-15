# REST API

The REST API provides standard HTTP endpoints for web dashboards and external integrations to interface with the agent factory.

*   **Location:** `src/api/`
*   **Framework:** FastAPI

## Multi-Surface Parity

The REST API is a thin transport adapter over the `src/core/` service layer. It contains no unique business logic. Any action you can perform via the REST API can also be performed via the CLI or MCP server.
