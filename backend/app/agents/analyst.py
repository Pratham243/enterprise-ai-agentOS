"""Analyst agent — specializes in data queries and numerical analysis.

This agent is the team's data analyst. When the orchestrator needs
numbers, aggregations, or database lookups, it delegates here.
"""

from backend.app.agents.base import AgentResult, BaseAgent
from backend.app.tools.sql_tool import SQLTool


class AnalystAgent(BaseAgent):
    """Queries the database to answer data and analytics questions."""

    def __init__(self) -> None:
        super().__init__(name="analyst_agent", tools=[SQLTool()])

    async def run(self, query: str) -> AgentResult:
        result = await super().run(query)
        result.steps.insert(0, {"agent": self.name, "role": "data_analysis"})
        return result
