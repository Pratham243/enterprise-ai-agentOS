"""MCP tool registry — standardized tool discovery and execution.

The Model Context Protocol (MCP) defines a uniform way for agents
to discover and invoke tools. Each tool registers itself with:
- name: unique identifier
- description: what the tool does (an LLM reads this to decide when to use it)
- input_schema: JSON Schema describing the expected input
- a run function

Any MCP-compatible agent can then list available tools and call them
by name, without knowing their implementation details.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable


@dataclass
class MCPToolDefinition:
    """A tool registered in the MCP registry."""

    name: str
    description: str
    input_schema: dict
    handler: Callable[[dict], Awaitable[str]]


class MCPRegistry:
    """Central registry for MCP-compatible tools."""

    def __init__(self) -> None:
        self._tools: dict[str, MCPToolDefinition] = {}

    def register(self, tool: MCPToolDefinition) -> None:
        """Register a tool in the registry."""
        self._tools[tool.name] = tool

    def list_tools(self) -> list[dict]:
        """Return all tools in MCP discovery format."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
            }
            for t in self._tools.values()
        ]

    async def execute(self, tool_name: str, arguments: dict) -> dict:
        """Execute a tool by name with the given arguments.

        Returns:
            {"result": "..."} on success
            {"error": "..."} on failure
        """
        tool = self._tools.get(tool_name)
        if not tool:
            return {"error": f"Tool not found: {tool_name}"}

        try:
            result = await tool.handler(arguments)
            return {"result": result}
        except Exception as e:
            return {"error": str(e)}

    @property
    def count(self) -> int:
        return len(self._tools)


# --- Shared registry instance -------------------------------------------------
mcp_registry = MCPRegistry()


def _register_default_tools() -> None:
    """Register the built-in tools with MCP-compatible schemas."""
    from backend.app.tools.rag_tool import RAGTool
    from backend.app.tools.sql_tool import SQLTool

    rag = RAGTool()
    sql = SQLTool()

    mcp_registry.register(MCPToolDefinition(
        name="document_search",
        description=rag.description,
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
            },
            "required": ["query"],
        },
        handler=lambda args: rag.run(args["query"]),
    ))

    mcp_registry.register(MCPToolDefinition(
        name="sql_query",
        description=sql.description,
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "SQL SELECT statement"},
            },
            "required": ["query"],
        },
        handler=lambda args: sql.run(args["query"]),
    ))


_register_default_tools()
