"""Research agent — specializes in document search and knowledge retrieval.

This agent is the team's librarian. When the orchestrator needs
information from company documents, policies, or reports, it
delegates to the research agent.
"""

from backend.app.agents.base import AgentResult, BaseAgent
from backend.app.tools.rag_tool import RAGTool


class ResearchAgent(BaseAgent):
    """Searches ingested documents to answer knowledge questions."""

    def __init__(self) -> None:
        super().__init__(name="research_agent", tools=[RAGTool()])

    async def run(self, query: str) -> AgentResult:
        result = await super().run(query)
        result.steps.insert(0, {"agent": self.name, "role": "document_research"})
        return result
