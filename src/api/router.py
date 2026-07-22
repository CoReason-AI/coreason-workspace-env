from fastapi import APIRouter
from src.api.endpoints import agents, health, skills, sandboxes

api_router = APIRouter()

# Register the REST endpoints
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_router.include_router(skills.router, prefix="/skills", tags=["Skills"])
api_router.include_router(sandboxes.router, prefix="/sandboxes", tags=["Sandboxes"])

@api_router.get("/status/{session_id}", tags=["Factory"])
async def get_factory_status(session_id: str):
    from src.core.services import agent_service
    status = await agent_service.get_execution_status(session_id)
    return {"session_id": session_id, "status": status}
