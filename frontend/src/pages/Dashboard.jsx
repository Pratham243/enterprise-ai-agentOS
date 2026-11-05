import { useEffect, useState } from "react";
import { api } from "../services/api";
import Spinner from "../components/Spinner";
import Toast from "../components/Toast";

export default function Dashboard() {
  const [health, setHealth] = useState(null);
  const [tools, setTools] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api.health().then(setHealth).catch((e) => setError(e.message));
    api.mcpListTools().then((d) => setTools(d.tools || [])).catch(() => {});
  }, []);

  return (
    <div className="page">
      <h2>Dashboard</h2>

      {error && (
        <Toast message={error} type="error" onClose={() => setError("")} />
      )}

      <div className="grid">
        <div className="card">
          <h3>System Health</h3>
          {health ? (
            <>
              <p className="stat-value">{health.status}</p>
              <p className="stat-label">{health.app}</p>
            </>
          ) : (
            <div className="loading-row"><Spinner size={18} /> Connecting...</div>
          )}
        </div>

        <div className="card">
          <h3>MCP Tools</h3>
          <p className="stat-value">{tools.length}</p>
          <p className="stat-label">registered tools</p>
        </div>

        <div className="card">
          <h3>Architecture</h3>
          <p className="stat-value">3</p>
          <p className="stat-label">AI agents (Orchestrator, Research, Analyst)</p>
        </div>

        <div className="card">
          <h3>Pipelines</h3>
          <p className="stat-value">2</p>
          <p className="stat-label">RAG + SQL workflow paths</p>
        </div>
      </div>

      <div className="card" style={{ marginTop: "1.5rem" }}>
        <h3>Quick Overview</h3>
        <table className="info-table">
          <tbody>
            <tr><td>API Framework</td><td>FastAPI + Uvicorn</td></tr>
            <tr><td>Database</td><td>PostgreSQL (SQLite for dev)</td></tr>
            <tr><td>Vector DB</td><td>Pinecone (in-memory for dev)</td></tr>
            <tr><td>LLM Provider</td><td>OpenAI / Azure OpenAI (mock for dev)</td></tr>
            <tr><td>Orchestration</td><td>LangGraph-style graph engine</td></tr>
            <tr><td>Authentication</td><td>JWT (disabled in dev)</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
