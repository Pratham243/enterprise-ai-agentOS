import { useState } from "react";
import { api } from "../services/api";

export default function Evaluate() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim() || !answer.trim()) return;
    setLoading(true);
    try {
      const data = await api.evaluateResponse(question, answer);
      setResult(data);
    } catch (err) {
      setResult({ error: err.message });
    } finally {
      setLoading(false);
    }
  };

  const scoreBar = (label, score) => (
    <div className="score-row">
      <span className="score-label">{label}</span>
      <div className="score-bar-bg">
        <div
          className="score-bar-fill"
          style={{ width: `${(score * 100).toFixed(0)}%` }}
        />
      </div>
      <span className="score-value">{(score * 100).toFixed(0)}%</span>
    </div>
  );

  return (
    <div className="page">
      <h2>Response Evaluation</h2>

      <div className="grid two-col">
        <div className="card">
          <h3>Input</h3>
          <form onSubmit={handleSubmit}>
            <label>Question</label>
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="What is RAG?"
            />
            <label>Answer to evaluate</label>
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="RAG is retrieval-augmented generation..."
              rows={5}
            />
            <button type="submit" disabled={loading || !question.trim() || !answer.trim()}>
              Evaluate
            </button>
          </form>
        </div>

        <div className="card">
          <h3>Scores</h3>
          {!result && <p className="empty-state">Submit a Q&A pair to evaluate.</p>}
          {result && !result.error && (
            <>
              <div className="overall-score">
                <span className="stat-value">
                  {(result.overall_score * 100).toFixed(0)}%
                </span>
                <span className="stat-label">overall</span>
              </div>

              {scoreBar("Relevance", result.relevance_score || 0)}
              {scoreBar("Completeness", result.completeness_score || 0)}
              {scoreBar("Safety", result.safety_score || 0)}

              {result.feedback && (
                <div className="feedback-box">
                  <h4>Feedback</h4>
                  <ul>
                    {result.feedback.map((f, i) => (
                      <li key={i}>{f}</li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
          {result?.error && <div className="result error">{result.error}</div>}
        </div>
      </div>
    </div>
  );
}
