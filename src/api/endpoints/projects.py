from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_projects():
    """List all projects in the workspace."""
    return {"projects": []}

@router.post("/")
async def create_project():
    """Create a new project plugin via project.yaml."""
    return {"status": "created"}
