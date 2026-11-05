"""Orchestrator — coordinates multiple specialist agents.

The orchestrator is the team manager. It:
1. Receives a question from the user
2. Decides which specialist(s) to involve
3. Delegates subtasks to them
4. Collects and merges their results
5. Returns a unified answer

In a future step, an LLM will make the delegation decisions.
For now, the orchestrator uses the same keyword-based classifier.
"""

from dataclasses import dataclass, field

from backend.app.agents.base import AgentResult, BaseAgent
from backend.app.agents.router import _classify


@dataclass
class MultiAgentResult:
    """The combined result from multiple agents."""

    question: str
    answer: str
    agents_used: list[str] = field(default_factory=list)
    agent_results: list[dict] = field(default_factory=list)
    steps: list[dict] = field(default_factory=list)


class Orchestrator:
    """Multi-agent coordinator.

    Register specialist agents, then call run() with a question.
    The orchestrator decides which agents to involve and compiles
    their outputs.
    """

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}

    def register(self, category: str, agent: BaseAgent) -> None:
        """Register a specialist agent for a category."""
        self._agents[category] = agent

    @property
    def available_agents(self) -> list[str]:
        return list(self._agents.keys())

    async def run(self, question: str) -> MultiAgentResult:
        """Route a question to the right specialist and return the result."""
        category = _classify(question)
        steps = [{"action": "orchestrate", "category": category}]

        agent = self._agents.get(category)
        if not agent:
            return MultiAgentResult(
                question=question,
                answer=f"No agent registered for category: {category}",
                steps=steps,
            )

        result: AgentResult = await agent.run(question)

        return MultiAgentResult(
            question=question,
            answer=result.answer,
            agents_used=[agent.name],
            agent_results=[{
                "agent": agent.name,
                "tool_used": result.tool_used,
                "output": result.answer,
            }],
            steps=steps + result.steps,
        )
