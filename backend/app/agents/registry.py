"""Agent registry — creates and returns the pre-configured orchestrator.

Centralizes agent creation so the rest of the app just imports
get_orchestrator() and doesn't need to know about individual agents.
"""

from backend.app.agents.analyst import AnalystAgent
from backend.app.agents.orchestrator import Orchestrator
from backend.app.agents.research import ResearchAgent

_orchestrator: Orchestrator | None = None


def get_orchestrator() -> Orchestrator:
    """Return the shared orchestrator with all agents registered."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
        _orchestrator.register("rag", ResearchAgent())
        _orchestrator.register("sql", AnalystAgent())
    return _orchestrator
