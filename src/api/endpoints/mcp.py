"""
REST API — MCP Server endpoints.
Delegated natively to DeepAgents MCP.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()

class ExecuteToolRequest(BaseModel):
    server_name: str = Field(..., description="Name of the MCP server")
    tool_name: str = Field(..., description="Name of the MCP tool to execute")
    arguments: dict = Field(default_factory=dict, description="Tool arguments")
    session_id: str = Field("default", description="Session ID for RBAC/escalation")

@router.get("/servers")
async def list_mcp_servers():
    """List connected MCP Servers."""
    # Natively supported by DeepAgents in future
    return {"servers": []}

@router.post("/execute_tool")
async def execute_mcp_tool(req: ExecuteToolRequest):
    """Execute a tool via MCP."""
    return {"status": "error", "detail": "Delegated to native DeepAgents MCP"}
