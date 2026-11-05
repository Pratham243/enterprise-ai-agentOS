"""Base tool interface.

Every tool an agent can use implements this interface. A tool has:
- A name (so the agent can refer to it)
- A description (so the agent knows when to use it)
- A run() method that takes an input string and returns a result string

This is the same pattern used by LangChain, CrewAI, and other agent
frameworks — so when we plug in real LLM orchestration later, the
tools will be ready.
"""

from abc import ABC, abstractmethod


class BaseTool(ABC):
    """Abstract base class for all agent tools."""

    name: str
    description: str

    @abstractmethod
    async def run(self, input_text: str) -> str:
        """Execute the tool and return a text result."""
        ...
