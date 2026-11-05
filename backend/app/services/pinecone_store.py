"""Pinecone vector store — production-ready vector database client.

Uses Pinecone when PINECONE_API_KEY is configured, otherwise falls back
to the InMemoryVectorStore so everything works without credentials.

Usage:
    from backend.app.services.pinecone_store import vector_store

    vector_store.upsert(ids, embeddings, texts, metadatas)
    results = vector_store.query(embedding, top_k=5)
"""

import logging

from backend.app.config import settings
from backend.app.services.vector_store import InMemoryVectorStore, SearchResult

logger = logging.getLogger(__name__)


class PineconeVectorStore:
    """Thin wrapper around the Pinecone SDK."""

    def __init__(self) -> None:
        from pinecone import Pinecone

        pc = Pinecone(api_key=settings.pinecone_api_key)
        self._index = pc.Index(settings.pinecone_index_name)
        logger.info(
            "Vector store: Pinecone (index=%s)", settings.pinecone_index_name
        )

    def upsert(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        texts: list[str],
        metadatas: list[dict] | None = None,
    ) -> int:
        """Upsert vectors into Pinecone."""
        metadatas = metadatas or [{} for _ in ids]
        vectors = []
        for vid, emb, text, meta in zip(ids, embeddings, texts, metadatas):
            meta_with_text = {**meta, "text": text}
            vectors.append({"id": vid, "values": emb, "metadata": meta_with_text})

        self._index.upsert(vectors=vectors)
        return len(vectors)

    def query(
        self,
        embedding: list[float],
        top_k: int = 5,
    ) -> list[SearchResult]:
        """Query Pinecone for similar vectors."""
        response = self._index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True,
        )
        results = []
        for match in response.matches:
            text = match.metadata.pop("text", "")
            results.append(
                SearchResult(
                    id=match.id,
                    score=match.score,
                    text=text,
                    metadata=match.metadata,
                )
            )
        return results

    @property
    def count(self) -> int:
        """Approximate vector count from Pinecone stats."""
        stats = self._index.describe_index_stats()
        return stats.total_vector_count


def _create_vector_store() -> InMemoryVectorStore | PineconeVectorStore:
    """Select the appropriate vector store based on configuration."""
    if settings.pinecone_api_key:
        try:
            return PineconeVectorStore()
        except ImportError:
            logger.warning("pinecone package not installed; using in-memory store")
        except Exception as e:
            logger.warning("Failed to connect to Pinecone (%s); using in-memory store", e)

    logger.info("No Pinecone API key configured; using in-memory vector store")
    return InMemoryVectorStore()


vector_store = _create_vector_store()
