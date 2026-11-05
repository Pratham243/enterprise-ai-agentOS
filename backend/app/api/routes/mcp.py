"""MCP API endpoints — tool discovery and execution.

GET  /mcp/tools    — list all available tools with their schemas
POST /mcp/execute  — call a tool by name with arguments
"""

from pydantic import BaseModel, Field
from fastapi import APIRouter

from backend.app.mcp.registry import mcp_registry

router = APIRouter(prefix="/mcp", tags=["MCP"])


class ExecuteRequest(BaseModel):
    tool_name: str = Field(..., max_length=200, description="Name of the tool to execute")
    arguments: dict = Field(default_factory=dict, description="Tool input arguments")


class ExecuteResponse(BaseModel):
    tool_name: str
    result: str | None = None
    error: str | None = None


@router.get("/tools")
async def list_tools() -> list[dict]:
    """Discover all MCP-registered tools and their input schemas."""
    return mcp_registry.list_tools()


@router.post("/execute", response_model=ExecuteResponse)
async def execute_tool(request: ExecuteRequest) -> ExecuteResponse:
    """Execute an MCP tool by name."""
    output = await mcp_registry.execute(request.tool_name, request.arguments)
    return ExecuteResponse(
        tool_name=request.tool_name,
        result=output.get("result"),
        error=output.get("error"),
    )
