from fastapi import APIRouter

from src.api.endpoints import projects, agents, mcp, docs, health
from src.api.streaming import crdt, state_sync

api_router = APIRouter()

from fastapi import Depends
from src.api.auth import get_current_user

# Register the REST endpoints
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"], dependencies=[Depends(get_current_user)])
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"], dependencies=[Depends(get_current_user)])
api_router.include_router(mcp.router, prefix="/mcp", tags=["Model Context Protocol"], dependencies=[Depends(get_current_user)])
api_router.include_router(docs.router, prefix="/docs", tags=["Documentation Service"], dependencies=[Depends(get_current_user)])

from fastapi import HTTPException
from fastapi.responses import FileResponse

@api_router.post("/export/{session_id}", tags=["Factory"], dependencies=[Depends(get_current_user)])
async def export_platform(session_id: str):
    import re
    if not re.match(r"^[a-zA-Z0-9_-]+$", session_id):
        raise HTTPException(status_code=400, detail="Invalid session_id")
    safe_session_id = session_id
    from src.core.services.export_service import PlatformExporter
    exporter = PlatformExporter()
    zip_path = await exporter.bundle_agent_specs(safe_session_id)
    if not zip_path:
        raise HTTPException(status_code=404, detail="Artifact not found for session")
    return FileResponse(zip_path, media_type="application/zip", filename=f"{safe_session_id}.zip")

@api_router.get("/status/{session_id}", tags=["Factory"], dependencies=[Depends(get_current_user)])
async def get_factory_status(session_id: str):
    from src.core.services import agent_service
    status = agent_service.get_execution_status(session_id)
    return {"session_id": session_id, "status": status}

# Register the Streaming endpoints (WebSocket/SSE)
api_router.include_router(crdt.router, prefix="/ws", tags=["Streaming: CRDT"], dependencies=[Depends(get_current_user)])
api_router.include_router(state_sync.router, prefix="/ws", tags=["Streaming: State Sync"], dependencies=[Depends(get_current_user)])
