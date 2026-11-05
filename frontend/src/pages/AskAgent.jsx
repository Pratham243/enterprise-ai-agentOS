import { useState, useRef, useCallback } from "react";
import { api } from "../services/api";
import Spinner from "../components/Spinner";
import Toast from "../components/Toast";

export default function AskAgent() {
  const [question, setQuestion] = useState("");
  const [mode, setMode] = useState("stream");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [liveSteps, setLiveSteps] = useState([]);
  const [toast, setToast] = useState(null);
  const wsRef = useRef(null);

  const handleStream = useCallback(
    (q) => {
      const ws = new WebSocket(api.getAgentWebSocketUrl());
      wsRef.current = ws;
      setLiveSteps([]);

      ws.onopen = () => {
        ws.send(JSON.stringify({ question: q }));
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === "step") {
          setLiveSteps((prev) => [
            ...prev,
            { node: data.node, data: data.data },
          ]);
        } else if (data.type === "complete") {
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content: data.answer,
              steps: data.steps,
              category: data.category,
              streamed: true,
            },
          ]);
          setLiveSteps([]);
          setLoading(false);
          ws.close();
        } else if (data.type === "error") {
          setMessages((prev) => [
            ...prev,
            { role: "error", content: data.detail },
          ]);
          setLiveSteps([]);
          setLoading(false);
          ws.close();
        }
      };

      ws.onerror = () => {
        setMessages((prev) => [
          ...prev,
          { role: "error", content: "WebSocket connection failed" },
        ]);
        setLiveSteps([]);
        setLoading(false);
      };

      ws.onclose = () => {
        wsRef.current = null;
      };
    },
    [],
  );

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim() || loading) return;

    const q = question.trim();
    setMessages((prev) => [...prev, { role: "user", content: q }]);
    setQuestion("");
    setLoading(true);

    if (mode === "stream") {
      handleStream(q);
      return;
    }

    try {
      let data;
      if (mode === "workflow") {
        data = await api.workflowRun(q);
      } else if (mode === "agent") {
        data = await api.agentQuery(q);
      } else {
        data = await api.multiAgentQuery(q);
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer,
          steps: data.steps,
          category: data.category,
          tool_used: data.tool_used,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "error", content: err.message },
      ]);
      setToast({ message: err.message, type: "error" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
      <h2>Ask Agent</h2>

      <div className="mode-selector">
        {[
          ["stream", "Stream (Live)"],
          ["workflow", "Workflow (Graph)"],
          ["agent", "Single Agent"],
          ["multi", "Multi-Agent"],
        ].map(([value, label]) => (
          <button
            key={value}
            className={`mode-btn ${mode === value ? "active" : ""}`}
            onClick={() => setMode(value)}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="chat-container">
        {messages.length === 0 && !loading && (
          <p className="chat-empty">
            Ask a question about your data. Try &quot;What is the refund policy?&quot; or
            &quot;How many audit logs are there?&quot;
          </p>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`chat-msg ${msg.role}`}>
            <div className="chat-msg-content">{msg.content}</div>
            {msg.steps && (
              <details className="chat-details">
                <summary>Processing steps ({msg.steps.length})</summary>
                <pre>{JSON.stringify(msg.steps, null, 2)}</pre>
              </details>
            )}
            {msg.category && (
              <span className="chat-badge">Route: {msg.category}</span>
            )}
            {msg.tool_used && (
              <span className="chat-badge">Tool: {msg.tool_used}</span>
            )}
            {msg.streamed && (
              <span className="chat-badge stream-badge">Streamed</span>
            )}
          </div>
        ))}

        {liveSteps.length > 0 && (
          <div className="chat-msg assistant streaming">
            <div className="live-steps">
              {liveSteps.map((step, i) => (
                <div key={i} className="live-step">
                  <span className="live-step-dot" />
                  <strong>{step.node}</strong>
                  <span className="live-step-data">
                    {JSON.stringify(step.data).slice(0, 120)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {loading && liveSteps.length === 0 && (
          <div className="chat-msg assistant loading">
            <div className="loading-row"><Spinner size={18} /> Connecting...</div>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="chat-input-row">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question..."
          disabled={loading}
        />
        <button type="submit" disabled={loading || !question.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
