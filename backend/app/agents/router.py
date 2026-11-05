"""Agent router — picks the right agent for a given question.

In an enterprise platform, different questions need different specialists:
- "What does the policy say about refunds?" → RAG agent (document search)
- "How many orders were placed last month?" → SQL agent (database query)

The router inspects the question and routes it to the appropriate agent.
In a later step, an LLM will do this classification. For now we use
simple keyword matching.
"""

from backend.app.agents.base import AgentResult, BaseAgent
from backend.app.tools.rag_tool import RAGTool
from backend.app.tools.sql_tool import SQLTool

# Pre-built specialist agents
_rag_agent = BaseAgent(name="document_agent", tools=[RAGTool()])
_sql_agent = BaseAgent(name="sql_agent", tools=[SQLTool()])

# Keywords that suggest a SQL/data question
_SQL_KEYWORDS = {
    "how many", "count", "total", "sum", "average", "select",
    "query", "database", "table", "rows", "max", "min",
}


def _classify(question: str) -> str:
    """Classify a question as 'sql' or 'rag'."""
    lower = question.lower()
    words = set(lower.split())
    for keyword in _SQL_KEYWORDS:
        # Multi-word keywords: substring match. Single-word: whole-word match.
        if " " in keyword:
            if keyword in lower:
                return "sql"
        elif keyword in words:
            return "sql"
    return "rag"


async def route_query(question: str) -> AgentResult:
    """Route a question to the right agent and return the result."""
    category = _classify(question)
    agent = _sql_agent if category == "sql" else _rag_agent
    result = await agent.run(question)
    result.steps.insert(0, {"action": "route", "category": category, "agent": agent.name})
    return result
