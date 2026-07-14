from fastapi import APIRouter

router = APIRouter()

@router.get("/servers")
async def list_mcp_servers():
    """List connected MCP Servers."""
    return {"servers": []}

@router.post("/execute_tool")
async def execute_mcp_tool():
    """Execute a tool via MCP."""
    return {"result": "success"}
