from fastapi import APIRouter

from src.api.endpoints import agents, health

api_router = APIRouter()

# Register the REST endpoints
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])

@api_router.get("/status/{session_id}", tags=["Factory"])
async def get_factory_status(session_id: str):
    from src.core.services import agent_service
    status = agent_service.get_execution_status(session_id)
    return {"session_id": session_id, "status": status}
