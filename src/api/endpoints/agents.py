from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_agents():
    """List all agents across projects."""
    return {"agents": []}

@router.post("/execute")
async def execute_agent_workflow():
    """Trigger a LangGraph execution flow."""
    return {"status": "enqueued"}
