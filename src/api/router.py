from fastapi import APIRouter

from src.api.endpoints import projects, agents, mcp, ws

api_router = APIRouter()

# Register the REST endpoints
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_router.include_router(mcp.router, prefix="/mcp", tags=["Model Context Protocol"])

# Register the WebSocket endpoints for the Edge Proxy
api_router.include_router(ws.router, prefix="/ws", tags=["WebSockets"])
