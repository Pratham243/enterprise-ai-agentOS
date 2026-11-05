"""Tests for Step 16: Production clients — LLM, embeddings, vector store, auth."""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app
from backend.app.services.llm_client import MockLLMClient, LLMResponse


# --- LLM Client (mock mode) --------------------------------------------------

async def test_mock_llm_chat():
    client = MockLLMClient()
    response = await client.chat("Hello world")
    assert isinstance(response, LLMResponse)
    assert response.model == "mock-llm-v1"
    assert "Hello world" in response.content


async def test_mock_llm_classification():
    client = MockLLMClient()
    response = await client.chat(
        "how many users are there?",
        system="Classify this question by category.",
    )
    assert "sql" in response.content


async def test_mock_llm_chat_json():
    client = MockLLMClient()
    result = await client.chat_json(
        "how many orders this month?",
        system="Classify this question by category.",
    )
    assert isinstance(result, dict)
    assert result.get("category") == "sql"


async def test_mock_llm_rag_classification():
    client = MockLLMClient()
    result = await client.chat_json(
        "What is the refund policy?",
        system="Classify this question by category.",
    )
    assert result.get("category") == "rag"


# --- Embeddings (mock mode) --------------------------------------------------

def test_embeddings_deterministic():
    from backend.app.services.embeddings import get_embedding
    v1 = get_embedding("test text")
    v2 = get_embedding("test text")
    assert v1 == v2


def test_embeddings_batch():
    from backend.app.services.embeddings import get_embeddings_batch
    vectors = get_embeddings_batch(["hello", "world"])
    assert len(vectors) == 2
    assert len(vectors[0]) > 0
    assert vectors[0] != vectors[1]


# --- Vector Store (in-memory fallback) ----------------------------------------

def test_vector_store_fallback():
    from backend.app.services.vector_store import InMemoryVectorStore
    store = InMemoryVectorStore()
    store.upsert(
        ids=["v1"],
        embeddings=[[0.1, 0.2, 0.3]],
        texts=["test doc"],
    )
    assert store.count == 1
    results = store.query([0.1, 0.2, 0.3], top_k=1)
    assert len(results) == 1
    assert results[0].text == "test doc"


# --- Auth (dev mode — no JWT_SECRET_KEY) --------------------------------------

async def test_auth_dev_mode():
    from backend.app.api.auth import get_current_user
    user = await get_current_user(credentials=None)
    assert user["sub"] == "dev-user"
    assert user["role"] == "admin"


# --- Workflow still works end-to-end ------------------------------------------

async def test_workflow_with_llm_nodes():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/workflow/run", json={
            "question": "What is the refund policy?",
        })
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "steps" in data


async def test_agent_query_still_works():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/agent/query", json={
            "question": "How many audit logs are there?",
        })
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
