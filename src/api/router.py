from fastapi import APIRouter

from src.api.endpoints import projects, agents, mcp, health
from src.api.streaming import events

api_router = APIRouter()

# Register the REST endpoints
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_router.include_router(mcp.router, prefix="/mcp", tags=["Model Context Protocol"])

# Register the Streaming endpoints (WebSocket/SSE)
api_router.include_router(events.router, prefix="/ws", tags=["Streaming: Events"])
