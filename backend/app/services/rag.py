"""RAG service — the core retrieval-augmented generation pipeline.

Orchestrates the full flow:
1. Accept a document → chunk it → embed chunks → store in vector DB.
2. Accept a question → embed it → retrieve relevant chunks → return context.

The LLM generation step (sending context + question to an LLM) will be
added in Step 5 when we build agents. For now, retrieval is the focus.
"""

import uuid

from backend.app.services.document_processor import chunk_text
from backend.app.services.embeddings import get_embedding, get_embeddings_batch
from backend.app.services.vector_store import SearchResult, vector_store


def ingest_document(text: str, source: str = "unknown") -> int:
    """Chunk a document, embed it, and store in the vector database.

    Args:
        text: Full document text.
        source: Identifier for where the document came from.

    Returns:
        Number of chunks stored.
    """
    chunks = chunk_text(text)
    if not chunks:
        return 0

    ids = [f"{source}_{uuid.uuid4().hex[:8]}" for _ in chunks]
    embeddings = get_embeddings_batch(chunks)
    metadatas = [{"source": source, "chunk_index": i} for i in range(len(chunks))]

    return vector_store.upsert(ids, embeddings, chunks, metadatas)


def retrieve(query: str, top_k: int = 5) -> list[SearchResult]:
    """Find the most relevant document chunks for a question.

    Args:
        query: The user's question.
        top_k: Number of results to return.

    Returns:
        Ranked list of relevant chunks with similarity scores.
    """
    query_embedding = get_embedding(query)
    return vector_store.query(query_embedding, top_k=top_k)
