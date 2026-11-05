import { useState } from "react";
import { api } from "../services/api";

const DEFAULT_FEATURES = {
  transaction_amount: 5000,
  account_age_days: 30,
  failed_logins: 2,
  country_risk: 0.3,
};

export default function RiskScoring() {
  const [entityId, setEntityId] = useState("txn-001");
  const [features, setFeatures] = useState({ ...DEFAULT_FEATURES });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const updateFeature = (key, value) => {
    setFeatures((prev) => ({ ...prev, [key]: parseFloat(value) || 0 }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data = await api.predictRisk(entityId, features);
      setResult(data);
    } catch (err) {
      setResult({ error: err.message });
    } finally {
      setLoading(false);
    }
  };

  const riskColor = (level) => {
    if (level === "high") return "var(--color-danger)";
    if (level === "medium") return "var(--color-warning)";
    return "var(--color-success)";
  };

  return (
    <div className="page">
      <h2>Risk Scoring</h2>

      <div className="grid two-col">
        <div className="card">
          <h3>Input Features</h3>
          <form onSubmit={handleSubmit}>
            <label>Entity ID</label>
            <input
              type="text"
              value={entityId}
              onChange={(e) => setEntityId(e.target.value)}
            />
            {Object.entries(features).map(([key, val]) => (
              <div key={key}>
                <label>{key.replace(/_/g, " ")}</label>
                <input
                  type="number"
                  step="any"
                  value={val}
                  onChange={(e) => updateFeature(key, e.target.value)}
                />
              </div>
            ))}
            <button type="submit" disabled={loading}>
              Predict Risk
            </button>
          </form>
        </div>

        <div className="card">
          <h3>Result</h3>
          {!result && <p className="empty-state">Submit features to see a prediction.</p>}
          {result && !result.error && (
            <>
              <div
                className="risk-badge"
                style={{ backgroundColor: riskColor(result.risk_level) }}
              >
                {result.risk_level?.toUpperCase()}
              </div>
              <p className="stat-value">{(result.risk_score * 100).toFixed(1)}%</p>
              <p className="stat-label">risk score</p>

              {result.explanations && result.explanations.length > 0 && (
                <>
                  <h4>Explanations (SHAP-style)</h4>
                  <ul className="explanation-list">
                    {result.explanations.map((exp, i) => (
                      <li key={i}>
                        <strong>{exp.feature}</strong>: {exp.direction} impact
                        ({exp.contribution > 0 ? "+" : ""}
                        {exp.contribution?.toFixed(3)})
                        <br />
                        <small>{exp.reason}</small>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </>
          )}
          {result?.error && <div className="result error">{result.error}</div>}
        </div>
      </div>
    </div>
  );
}
