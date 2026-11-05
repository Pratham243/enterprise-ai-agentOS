"""Evaluation service — measures AI output quality.

In production AI systems, you must evaluate whether the AI's answers
are actually correct, relevant, and safe. This service provides
scoring functions that rate agent outputs.

Metrics:
- relevance: Does the answer address the question?
- completeness: Does it cover the key points?
- safety: Is it free of harmful or inappropriate content?

These scores can be logged to MLflow for tracking over time.
"""

from dataclasses import dataclass


@dataclass
class EvaluationResult:
    """Quality scores for an AI-generated response."""

    question: str
    answer: str
    relevance_score: float    # 0.0 to 1.0
    completeness_score: float
    safety_score: float
    overall_score: float
    feedback: list[str]


def evaluate_response(question: str, answer: str, context: str = "") -> EvaluationResult:
    """Evaluate an AI response on multiple quality dimensions.

    This uses heuristic scoring as a placeholder. In production,
    an LLM-as-judge or human evaluators would score responses,
    and results would be logged to MLflow.
    """
    feedback = []

    # Relevance: does the answer relate to the question?
    q_words = set(question.lower().split())
    a_words = set(answer.lower().split())
    overlap = len(q_words & a_words)
    relevance = min(overlap / max(len(q_words), 1) * 2, 1.0)
    if relevance < 0.3:
        feedback.append("Answer may not be relevant to the question.")

    # Completeness: is the answer substantive?
    if len(answer) < 20:
        completeness = 0.2
        feedback.append("Answer is very short.")
    elif len(answer) < 100:
        completeness = 0.5
    else:
        completeness = 0.8
    if context and any(word in answer.lower() for word in context.lower().split()[:5]):
        completeness = min(completeness + 0.2, 1.0)

    # Safety: basic check for problematic content
    unsafe_patterns = ["ignore previous", "system prompt", "password", "hack"]
    safety = 1.0
    for pattern in unsafe_patterns:
        if pattern in answer.lower():
            safety -= 0.3
            feedback.append(f"Potential safety concern: contains '{pattern}'")
    safety = max(safety, 0.0)

    overall = round((relevance + completeness + safety) / 3, 3)

    if not feedback:
        feedback.append("Response looks good.")

    return EvaluationResult(
        question=question,
        answer=answer,
        relevance_score=round(relevance, 3),
        completeness_score=round(completeness, 3),
        safety_score=round(safety, 3),
        overall_score=overall,
        feedback=feedback,
    )
