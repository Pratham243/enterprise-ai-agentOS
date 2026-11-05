"""Tests for Steps 10-12: webhooks, risk model, and evaluation."""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app
from backend.app.services.evaluation import evaluate_response
from backend.app.services.risk_model import predict_risk


# --- Step 10: Webhooks --------------------------------------------------------

async def test_webhook_trigger():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/webhooks/trigger", json={
            "event": "new_ticket",
            "source": "n8n",
            "data": {"ticket_id": "T-123"},
        })
    assert response.status_code == 200
    data = response.json()
    assert data["event"] == "new_ticket"
    assert data["received"] is True


async def test_webhook_with_question():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/webhooks/trigger", json={
            "event": "scheduled_report",
            "question": "What is the refund policy?",
        })
    assert response.status_code == 200
    data = response.json()
    assert data["result"] is not None
    assert "answer" in data["result"]


# --- Step 11: Risk Model -----------------------------------------------------

def test_risk_low():
    result = predict_risk("user-1", {"transaction_amount": 100, "account_age_days": 500})
    assert result.risk_level == "low"
    assert result.risk_score < 0.4


def test_risk_high():
    result = predict_risk("user-2", {
        "transaction_amount": 15000,
        "account_age_days": 5,
        "failed_logins": 10,
        "country_risk": 0.9,
    })
    assert result.risk_level == "high"
    assert result.risk_score >= 0.7
    assert len(result.explanations) >= 3


async def test_risk_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/risk/predict", json={
            "entity_id": "txn-42",
            "features": {"transaction_amount": 8000, "account_age_days": 10},
        })
    assert response.status_code == 200
    data = response.json()
    assert data["entity_id"] == "txn-42"
    assert "risk_score" in data
    assert "explanations" in data


# --- Step 12: Evaluation -----------------------------------------------------

def test_evaluation_good_response():
    result = evaluate_response(
        question="What is Python?",
        answer="Python is a programming language widely used for AI, data science, and web development. It emphasizes readability.",
    )
    assert result.overall_score > 0.3
    assert result.safety_score == 1.0


def test_evaluation_short_response():
    result = evaluate_response(
        question="Explain machine learning",
        answer="It's AI.",
    )
    assert result.completeness_score <= 0.5


async def test_evaluation_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/evaluation/score", json={
            "question": "What is RAG?",
            "answer": "RAG is retrieval-augmented generation, a technique that combines document retrieval with LLM generation for grounded answers.",
        })
    assert response.status_code == 200
    data = response.json()
    assert "overall_score" in data
    assert "feedback" in data
