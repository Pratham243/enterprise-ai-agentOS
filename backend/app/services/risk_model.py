"""Risk model service — predictive scoring with explainability.

Provides a risk score for a given entity (customer, transaction, etc.)
along with feature-level explanations of what drove the score.

For now this uses rule-based scoring as a placeholder. In production:
- Train a real model (e.g., XGBoost or LightGBM)
- Use SHAP to explain predictions
- Track experiments with MLflow (Step 12)
"""

from dataclasses import dataclass, field


@dataclass
class RiskPrediction:
    """The result of a risk assessment."""

    entity_id: str
    risk_score: float  # 0.0 (safe) to 1.0 (high risk)
    risk_level: str    # "low", "medium", "high"
    explanations: list[dict] = field(default_factory=list)


def predict_risk(entity_id: str, features: dict) -> RiskPrediction:
    """Score an entity's risk based on its features.

    This is a rule-based placeholder. Replace with a trained ML model
    and SHAP explanations in production.

    Example features:
        {"transaction_amount": 5000, "account_age_days": 30,
         "failed_logins": 3, "country_risk": 0.7}
    """
    score = 0.0
    explanations = []

    # Rule 1: High transaction amount
    amount = features.get("transaction_amount", 0)
    if amount > 10000:
        contribution = 0.3
        score += contribution
        explanations.append({
            "feature": "transaction_amount",
            "value": amount,
            "contribution": contribution,
            "reason": "Transaction amount exceeds $10,000 threshold",
        })
    elif amount > 5000:
        contribution = 0.15
        score += contribution
        explanations.append({
            "feature": "transaction_amount",
            "value": amount,
            "contribution": contribution,
            "reason": "Transaction amount exceeds $5,000 threshold",
        })

    # Rule 2: New account
    age = features.get("account_age_days", 365)
    if age < 30:
        contribution = 0.25
        score += contribution
        explanations.append({
            "feature": "account_age_days",
            "value": age,
            "contribution": contribution,
            "reason": "Account is less than 30 days old",
        })

    # Rule 3: Failed logins
    logins = features.get("failed_logins", 0)
    if logins > 5:
        contribution = 0.2
        score += contribution
        explanations.append({
            "feature": "failed_logins",
            "value": logins,
            "contribution": contribution,
            "reason": "High number of failed login attempts",
        })

    # Rule 4: Country risk
    country_risk = features.get("country_risk", 0.0)
    if country_risk > 0.5:
        contribution = country_risk * 0.25
        score += contribution
        explanations.append({
            "feature": "country_risk",
            "value": country_risk,
            "contribution": round(contribution, 3),
            "reason": "Elevated country risk factor",
        })

    # Cap at 1.0 and classify
    score = min(score, 1.0)
    if score >= 0.7:
        level = "high"
    elif score >= 0.4:
        level = "medium"
    else:
        level = "low"

    # Sort explanations by contribution (highest first) — like SHAP
    explanations.sort(key=lambda e: e["contribution"], reverse=True)

    return RiskPrediction(
        entity_id=entity_id,
        risk_score=round(score, 3),
        risk_level=level,
        explanations=explanations,
    )
