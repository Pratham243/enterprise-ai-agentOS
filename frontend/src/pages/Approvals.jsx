import { useEffect, useState } from "react";
import { api } from "../services/api";

export default function Approvals() {
  const [pending, setPending] = useState([]);
  const [loading, setLoading] = useState(true);
  const [reviewNote, setReviewNote] = useState("");
  const [reviewer, setReviewer] = useState("admin");

  const loadPending = async () => {
    setLoading(true);
    try {
      const data = await api.listPendingApprovals();
      setPending(data.items || []);
    } catch {
      setPending([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPending();
  }, []);

  const handleResolve = async (id, status) => {
    try {
      await api.resolveApproval(id, status, reviewer, reviewNote);
      setReviewNote("");
      loadPending();
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div className="page">
      <h2>Human-in-the-Loop Approvals</h2>

      <div className="card">
        <div className="card-header-row">
          <h3>Pending Requests</h3>
          <button onClick={loadPending} disabled={loading}>
            Refresh
          </button>
        </div>

        {loading && <p>Loading...</p>}

        {!loading && pending.length === 0 && (
          <p className="empty-state">No pending approvals.</p>
        )}

        {pending.map((req) => (
          <div key={req.id} className="approval-card">
            <div className="approval-header">
              <strong>{req.action}</strong>
              <span className="chat-badge">{req.agent_name || "unknown"}</span>
            </div>
            <p>{req.description}</p>
            <div className="approval-actions">
              <input
                type="text"
                value={reviewNote}
                onChange={(e) => setReviewNote(e.target.value)}
                placeholder="Review note (optional)"
              />
              <button
                className="btn-approve"
                onClick={() => handleResolve(req.id, "approved")}
              >
                Approve
              </button>
              <button
                className="btn-reject"
                onClick={() => handleResolve(req.id, "rejected")}
              >
                Reject
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
