from fastapi import APIRouter

from src.api.endpoints import projects, agents, mcp, docs
from src.api.streaming import crdt, tty, state_sync, agent_progress

api_router = APIRouter()

# Register the REST endpoints
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_router.include_router(mcp.router, prefix="/mcp", tags=["Model Context Protocol"])
api_router.include_router(docs.router, prefix="/docs", tags=["Documentation Service"])

# Register the Streaming endpoints (WebSocket/SSE)
api_router.include_router(crdt.router, prefix="/ws", tags=["Streaming: CRDT"])
api_router.include_router(tty.router, prefix="/ws", tags=["Streaming: TTY"])
api_router.include_router(state_sync.router, prefix="/ws", tags=["Streaming: State Sync"])
api_router.include_router(agent_progress.router, prefix="/ws", tags=["Streaming: Agent Progress"])
