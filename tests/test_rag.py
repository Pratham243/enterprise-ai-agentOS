"""Tests for the RAG pipeline — document processing, embeddings, and retrieval."""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app
from backend.app.services.document_processor import chunk_text
from backend.app.services.embeddings import EMBEDDING_DIM, get_embedding
from backend.app.services.vector_store import InMemoryVectorStore


# --- Unit tests for individual components -------------------------------------

def test_chunk_text_basic():
    """Text should be split into overlapping chunks."""
    text = "A" * 1200  # 1200 characters
    chunks = chunk_text(text, chunk_size=500, chunk_overlap=50)
    assert len(chunks) >= 3
    assert all(len(c) <= 500 for c in chunks)


def test_chunk_text_empty():
    """Empty text should return no chunks."""
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_embedding_dimension():
    """Embedding vectors must have the expected dimension."""
    vec = get_embedding("hello world")
    assert len(vec) == EMBEDDING_DIM
    assert all(isinstance(x, float) for x in vec)


def test_embedding_deterministic():
    """Same text should produce the same embedding."""
    a = get_embedding("test input")
    b = get_embedding("test input")
    assert a == b


def test_vector_store_upsert_and_query():
    """Store vectors and retrieve the most similar one."""
    store = InMemoryVectorStore()
    embeddings = [get_embedding(t) for t in ["cat", "dog", "car"]]
    store.upsert(
        ids=["1", "2", "3"],
        embeddings=embeddings,
        texts=["cat", "dog", "car"],
    )
    assert store.count == 3

    results = store.query(get_embedding("cat"), top_k=1)
    assert len(results) == 1
    assert results[0].text == "cat"
    assert results[0].score > 0


# --- API integration tests ----------------------------------------------------

@pytest.fixture(autouse=True)
def reset_vector_store():
    """Clear the global vector store between tests."""
    from backend.app.services.vector_store import vector_store
    vector_store._vectors.clear()


async def test_ingest_endpoint():
    """POST /rag/ingest should chunk and store a document."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/rag/ingest", json={
            "text": "This is a test document with enough text to be chunked properly. " * 20,
            "source": "test-doc",
        })
    assert response.status_code == 200
    data = response.json()
    assert data["chunks_stored"] >= 1
    assert data["source"] == "test-doc"


async def test_query_endpoint():
    """POST /rag/query should return results after ingestion."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First ingest a document
        await client.post("/rag/ingest", json={
            "text": "Python is a programming language used for AI and data science. " * 20,
            "source": "python-doc",
        })
        # Then query
        response = await client.post("/rag/query", json={
            "question": "What is Python?",
            "top_k": 3,
        })
    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "What is Python?"
    assert len(data["results"]) >= 1
    assert "text" in data["results"][0]
    assert "score" in data["results"][0]
