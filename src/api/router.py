from fastapi import APIRouter

from src.api.endpoints import projects, agents, mcp, ws, docs

api_router = APIRouter()

# Register the REST endpoints
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_router.include_router(mcp.router, prefix="/mcp", tags=["Model Context Protocol"])
api_router.include_router(docs.router, prefix="/docs", tags=["Documentation Service"])

# Register the WebSocket endpoints for the Edge Proxy
api_router.include_router(ws.router, prefix="/ws", tags=["WebSockets"])
