"""Embedding service — converts text into vector representations.

Supports:
- OpenAI embeddings (text-embedding-3-small) when OPENAI_API_KEY is set
- Azure OpenAI embeddings when Azure credentials are set
- Mock fallback (deterministic hash-based) when no API key is available

Usage:
    from backend.app.services.embeddings import get_embedding, get_embeddings_batch

    vector = get_embedding("What is Python?")
    vectors = get_embeddings_batch(["text one", "text two"])
"""

import hashlib
import logging
import math

from backend.app.config import settings

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 256
_openai_client = None
_embedding_model = "text-embedding-3-small"
_use_real_embeddings = False


def _init_openai_embeddings() -> bool:
    """Try to set up real OpenAI embeddings. Returns True on success."""
    global _openai_client, _use_real_embeddings, _embedding_model

    has_openai = bool(settings.openai_api_key)
    has_azure = bool(settings.azure_openai_api_key and settings.azure_openai_endpoint)

    if not (has_openai or has_azure):
        return False

    try:
        from openai import OpenAI, AzureOpenAI

        if has_azure:
            _openai_client = AzureOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                api_version="2024-10-21",
            )
            _embedding_model = settings.azure_openai_deployment or "text-embedding-3-small"
            logger.info("Embeddings: Azure OpenAI (%s)", _embedding_model)
        else:
            _openai_client = OpenAI(api_key=settings.openai_api_key)
            logger.info("Embeddings: OpenAI (%s)", _embedding_model)

        _use_real_embeddings = True
        return True
    except ImportError:
        logger.warning("openai package not installed; using mock embeddings")
        return False
    except Exception as e:
        logger.warning("Failed to init OpenAI embeddings (%s); using mock", e)
        return False


_init_openai_embeddings()


def _mock_embed(text: str) -> list[float]:
    """Generate a deterministic pseudo-embedding from text."""
    digest = hashlib.sha256(text.encode()).hexdigest()
    raw = [int(digest[i : i + 2], 16) / 255.0 for i in range(0, len(digest), 2)]
    vector = (raw * (EMBEDDING_DIM // len(raw) + 1))[:EMBEDDING_DIM]
    magnitude = math.sqrt(sum(x * x for x in vector))
    return [x / magnitude for x in vector]


def get_embedding(text: str) -> list[float]:
    """Return an embedding vector for the given text."""
    if _use_real_embeddings and _openai_client is not None:
        response = _openai_client.embeddings.create(
            model=_embedding_model,
            input=text,
        )
        return response.data[0].embedding

    return _mock_embed(text)


def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Return embedding vectors for a batch of texts."""
    if _use_real_embeddings and _openai_client is not None:
        response = _openai_client.embeddings.create(
            model=_embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    return [_mock_embed(t) for t in texts]
