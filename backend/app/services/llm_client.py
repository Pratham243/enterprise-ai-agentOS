"""LLM client — unified interface for calling language models.

Supports:
- OpenAI (gpt-4o, gpt-4o-mini, etc.)
- Azure OpenAI (same models, enterprise deployment)
- Mock fallback (when no API key is set — keeps tests working)

Usage:
    from backend.app.services.llm_client import llm

    response = await llm.chat("What is Python?")
    response = await llm.chat("Classify this question", system="You are a classifier.")
"""

import json
import logging
from dataclasses import dataclass

from backend.app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """The result of an LLM call."""

    content: str
    model: str
    usage: dict | None = None


class BaseLLMClient:
    """Abstract base for LLM clients."""

    async def chat(
        self,
        message: str,
        system: str = "",
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        raise NotImplementedError

    async def chat_json(
        self,
        message: str,
        system: str = "",
        temperature: float = 0.0,
    ) -> dict:
        """Call the LLM and parse the response as JSON."""
        response = await self.chat(
            message=message,
            system=system + "\nRespond with valid JSON only. No markdown, no explanation.",
            temperature=temperature,
        )
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            content = response.content
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
            return {"raw": content}


class OpenAIClient(BaseLLMClient):
    """Client for OpenAI and Azure OpenAI APIs."""

    def __init__(self) -> None:
        try:
            from openai import AsyncOpenAI, AsyncAzureOpenAI
        except ImportError:
            raise ImportError("Install openai: pip install openai")

        if settings.azure_openai_endpoint and settings.azure_openai_api_key:
            self._client = AsyncAzureOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                api_version="2024-10-21",
            )
            self._model = settings.azure_openai_deployment or "gpt-4o"
            self._provider = "azure"
            logger.info("LLM client: Azure OpenAI (%s)", self._model)
        else:
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)
            self._model = settings.openai_model
            self._provider = "openai"
            logger.info("LLM client: OpenAI (%s)", self._model)

    async def chat(
        self,
        message: str,
        system: str = "",
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": message})

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        choice = response.choices[0]
        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            usage=usage,
        )


class MockLLMClient(BaseLLMClient):
    """Mock LLM client for development and testing.

    Returns rule-based responses so the full pipeline works
    without an API key. Replace with OpenAI when keys are available.
    """

    async def chat(
        self,
        message: str,
        system: str = "",
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        lower = message.lower()

        # Classification requests
        if "classify" in system.lower() or "category" in system.lower():
            if any(w in lower for w in ["how many", "count", "total", "sum", "average"]):
                content = '{"category": "sql"}'
            else:
                content = '{"category": "rag"}'

        # SQL generation requests
        elif "sql" in system.lower() or "generate" in system.lower() and "query" in system.lower():
            content = "SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 10"

        # Synthesis requests
        elif "context" in lower and len(message) > 200:
            # Likely a synthesis request with retrieved context
            content = (
                "Based on the provided context, here is a synthesized answer: "
                + message[:200].split("---")[0].strip()
            )

        # General questions
        else:
            content = f"This is a mock LLM response to: {message[:100]}"

        return LLMResponse(content=content, model="mock-llm-v1")


def _create_client() -> BaseLLMClient:
    """Create the appropriate LLM client based on available configuration."""
    has_openai_key = bool(settings.openai_api_key)
    has_azure_key = bool(settings.azure_openai_api_key and settings.azure_openai_endpoint)

    if has_openai_key or has_azure_key:
        try:
            return OpenAIClient()
        except ImportError:
            logger.warning("openai package not installed; falling back to mock LLM")
        except Exception as e:
            logger.warning("Failed to create OpenAI client (%s); falling back to mock LLM", e)

    logger.info("No LLM API key configured; using mock LLM client")
    return MockLLMClient()


# Shared instance — import this wherever LLM calls are needed.
llm = _create_client()
