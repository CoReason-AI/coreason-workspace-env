# REST API

The CoReason Workspace Environment exposes a comprehensive **FastAPI-powered REST API**. 

Following the platform's Multi-Surface Parity mandate, the REST API does not duplicate business logic. It serves strictly as a transport adapter over the shared `src.core.services` layer, ensuring that operations triggered via HTTP behave identically to those triggered via the CLI or MCP server.

## Pydantic Schema Purity

All API payloads, models, and responses are strictly governed by the `coreason-manifest` PyPI package. 

- **No Local Schemas:** The platform natively forbids the creation of local schema files (e.g., `ontology.py` or `state.py`). All Pydantic geometry is imported directly from the immutable `coreason_manifest`.
- **Zero-Trust Validation:** The FastAPI router relies on these strict Pydantic definitions to mathematically reject malformed payloads before they ever reach the execution layer, enforcing the Epistemic Firewall at the network edge.

## UUIDv7 Primary Keys

The REST API utilizes UUIDv7 natively for all database primary keys and session identifiers (e.g., `snapshot_id`, `project_id`). 

Because UUIDv7 incorporates a Unix epoch timestamp in its most significant bits, it prevents Postgres B-Tree index fragmentation while providing native chronological sorting. You should expect all API endpoints to return and require UUIDv7 strings.

## Endpoints Overview

The API is fully self-documenting. When running the platform, you can view the Swagger UI at `http://localhost:8000/docs`.

### Core Router Spaces
- `/health`: System and dependency health checks.
- `/projects`: CRUD operations for agent projects.
- `/agents`: Agent execution, status polling, and definition retrieval.
- `/streaming`: HTTP-bound Server-Sent Events (SSE) and WebSocket upgrade endpoints for real-time observability.
