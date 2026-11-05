const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const WS_URL = BASE_URL.replace(/^http/, "ws");

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json();
}

export const api = {
  health: () => request("/health"),

  agentQuery: (question) =>
    request("/agent/query", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),

  workflowRun: (question) =>
    request("/workflow/run", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),

  ragIngest: (text, source) =>
    request("/rag/ingest", {
      method: "POST",
      body: JSON.stringify({ text, source }),
    }),

  ragQuery: (query, topK = 3) =>
    request("/rag/query", {
      method: "POST",
      body: JSON.stringify({ query, top_k: topK }),
    }),

  listPendingApprovals: () => request("/approvals/pending"),

  createApproval: (action, description, agentName) =>
    request("/approvals/", {
      method: "POST",
      body: JSON.stringify({
        action,
        description,
        agent_name: agentName,
      }),
    }),

  resolveApproval: (id, status, reviewer, reviewNote) =>
    request(`/approvals/${id}/resolve`, {
      method: "POST",
      body: JSON.stringify({
        status,
        reviewer,
        review_note: reviewNote,
      }),
    }),

  predictRisk: (entityId, features) =>
    request("/risk/predict", {
      method: "POST",
      body: JSON.stringify({ entity_id: entityId, features }),
    }),

  evaluateResponse: (question, answer) =>
    request("/evaluation/score", {
      method: "POST",
      body: JSON.stringify({ question, answer }),
    }),

  mcpListTools: () => request("/mcp/tools"),

  mcpExecute: (toolName, args) =>
    request("/mcp/execute", {
      method: "POST",
      body: JSON.stringify({ tool_name: toolName, arguments: args }),
    }),

  multiAgentQuery: (question) =>
    request("/multi-agent/query", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),

  getAgentWebSocketUrl: () => `${WS_URL}/ws/agent`,
};
