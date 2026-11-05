"""Vector store — abstraction over Pinecone for storing and querying embeddings.

This module provides a clean interface for:
1. Upserting document chunks with their embeddings into the vector database.
2. Querying for the most similar chunks given a question embedding.

For local development we use an in-memory store so no Pinecone API key
is needed. The interface stays the same — swap to real Pinecone later.
"""

from dataclasses import dataclass, field
import math


@dataclass
class SearchResult:
    """A single result from a vector similarity search."""

    id: str
    score: float
    text: str
    metadata: dict = field(default_factory=dict)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


class InMemoryVectorStore:
    """In-memory vector store for development and testing.

    In production this will be replaced by Pinecone:
        - pinecone.Index.upsert() for storing
        - pinecone.Index.query() for searching

    The API is intentionally similar to Pinecone's so the swap is easy.
    """

    def __init__(self) -> None:
        self._vectors: dict[str, dict] = {}

    def upsert(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        texts: list[str],
        metadatas: list[dict] | None = None,
    ) -> int:
        """Store vectors with their text and metadata.

        Returns the number of vectors upserted.
        """
        metadatas = metadatas or [{} for _ in ids]
        for vid, emb, text, meta in zip(ids, embeddings, texts, metadatas):
            self._vectors[vid] = {
                "embedding": emb,
                "text": text,
                "metadata": meta,
            }
        return len(ids)

    def query(
        self,
        embedding: list[float],
        top_k: int = 5,
    ) -> list[SearchResult]:
        """Find the top_k most similar vectors to the given embedding."""
        scored: list[tuple[str, float]] = []
        for vid, data in self._vectors.items():
            score = _cosine_similarity(embedding, data["embedding"])
            scored.append((vid, score))

        scored.sort(key=lambda x: x[1], reverse=True)

        results: list[SearchResult] = []
        for vid, score in scored[:top_k]:
            data = self._vectors[vid]
            results.append(
                SearchResult(
                    id=vid,
                    score=score,
                    text=data["text"],
                    metadata=data["metadata"],
                )
            )
        return results

    @property
    def count(self) -> int:
        """Number of vectors stored."""
        return len(self._vectors)


# Shared instance for the application
vector_store = InMemoryVectorStore()
