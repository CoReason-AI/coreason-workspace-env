"""
REST API — MCP Server endpoints.
Thin adapter over src.core.services.mcp_service.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.core.services import mcp_tool_service

router = APIRouter()


class ExecuteToolRequest(BaseModel):
    server_name: str = Field(..., description="Name of the MCP server")
    tool_name: str = Field(..., description="Name of the MCP tool to execute")
    arguments: dict = Field(default_factory=dict, description="Tool arguments")
    session_id: str = Field("default", description="Session ID for RBAC/escalation")


@router.get("/servers")
async def list_mcp_servers():
    """List connected MCP Servers."""
    servers = mcp_tool_service.list_servers()
    return {"servers": servers}


@router.post("/execute_tool")
async def execute_mcp_tool(req: ExecuteToolRequest):
    """Execute a tool via MCP."""
    result = await mcp_tool_service.execute_tool(
        server_name=req.server_name,
        tool_name=req.tool_name,
        arguments=req.arguments,
        session_id=req.session_id,
    )
    return result
