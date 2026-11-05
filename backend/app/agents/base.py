"""Base agent — the think → act → observe loop.

An agent receives a question, decides which tool(s) to use, calls them,
and compiles a final answer. This base class defines the pattern.

In a later step (Step 6), LangGraph will orchestrate more complex
multi-step flows. For now, this is a simple single-turn agent.
"""

from dataclasses import dataclass, field

from backend.app.tools.base import BaseTool


@dataclass
class AgentResult:
    """The outcome of an agent's work."""

    answer: str
    tool_used: str | None = None
    tool_input: str | None = None
    tool_output: str | None = None
    steps: list[dict] = field(default_factory=list)


class BaseAgent:
    """A single-purpose agent with access to one or more tools."""

    def __init__(self, name: str, tools: list[BaseTool]) -> None:
        self.name = name
        self.tools = {tool.name: tool for tool in tools}

    async def run(self, query: str) -> AgentResult:
        """Process a query using the agent's tools.

        For now this is a simple one-tool call. When we add LLM
        reasoning (Step 6), the agent will choose which tool to call
        and may chain multiple calls.
        """
        if not self.tools:
            return AgentResult(answer="No tools available.")

        # Use the first available tool (simple strategy for now)
        tool = next(iter(self.tools.values()))
        tool_output = await tool.run(query)

        return AgentResult(
            answer=tool_output,
            tool_used=tool.name,
            tool_input=query,
            tool_output=tool_output,
            steps=[
                {"action": "tool_call", "tool": tool.name, "input": query},
                {"action": "result", "output": tool_output},
            ],
        )
