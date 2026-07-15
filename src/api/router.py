from fastapi import APIRouter

from src.api.endpoints import projects, agents, mcp, docs, health
from src.api.streaming import crdt, tty, state_sync, agent_progress

api_router = APIRouter()

# Register the REST endpoints
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_router.include_router(mcp.router, prefix="/mcp", tags=["Model Context Protocol"])
api_router.include_router(docs.router, prefix="/docs", tags=["Documentation Service"])

from fastapi import HTTPException
from fastapi.responses import FileResponse

@api_router.post("/export/{session_id}", tags=["Factory"])
async def export_platform(session_id: str):
    from src.core.services.export_service import PlatformExporter
    exporter = PlatformExporter()
    zip_path = await exporter.bundle_agent_specs(session_id)
    if not zip_path:
        raise HTTPException(status_code=404, detail="Artifact not found for session")
    return FileResponse(zip_path, media_type="application/zip", filename=f"{session_id}.zip")

@api_router.get("/status/{session_id}", tags=["Factory"])
async def get_factory_status(session_id: str):
    from src.core.services import agent_service
    status = agent_service.get_execution_status(session_id)
    return {"session_id": session_id, "status": status}

# Register the Streaming endpoints (WebSocket/SSE)
api_router.include_router(crdt.router, prefix="/ws", tags=["Streaming: CRDT"])
api_router.include_router(tty.router, prefix="/ws", tags=["Streaming: TTY"])
api_router.include_router(state_sync.router, prefix="/ws", tags=["Streaming: State Sync"])
api_router.include_router(agent_progress.router, prefix="/ws", tags=["Streaming: Agent Progress"])
