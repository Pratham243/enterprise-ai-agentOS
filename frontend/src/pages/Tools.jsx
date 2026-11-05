import { useEffect, useState } from "react";
import { api } from "../services/api";

export default function Tools() {
  const [tools, setTools] = useState([]);
  const [selected, setSelected] = useState(null);
  const [args, setArgs] = useState("{}");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.mcpListTools().then((d) => setTools(d.tools || [])).catch(() => {});
  }, []);

  const handleExecute = async () => {
    if (!selected) return;
    setLoading(true);
    setResult(null);
    try {
      const parsed = JSON.parse(args);
      const data = await api.mcpExecute(selected.name, parsed);
      setResult(data);
    } catch (err) {
      setResult({ error: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <h2>MCP Tools</h2>

      <div className="grid two-col">
        <div className="card">
          <h3>Available Tools</h3>
          {tools.length === 0 && <p className="empty-state">No tools registered.</p>}
          {tools.map((tool) => (
            <div
              key={tool.name}
              className={`tool-card ${selected?.name === tool.name ? "active" : ""}`}
              onClick={() => {
                setSelected(tool);
                setResult(null);
                setArgs(
                  JSON.stringify(
                    Object.fromEntries(
                      Object.keys(tool.input_schema?.properties || {}).map((k) => [k, ""])
                    ),
                    null,
                    2
                  )
                );
              }}
            >
              <strong>{tool.name}</strong>
              <p>{tool.description}</p>
            </div>
          ))}
        </div>

        <div className="card">
          <h3>Execute Tool</h3>
          {!selected && <p className="empty-state">Select a tool from the list.</p>}
          {selected && (
            <>
              <h4>{selected.name}</h4>
              <p>{selected.description}</p>

              {selected.input_schema?.properties && (
                <details>
                  <summary>Input schema</summary>
                  <pre>{JSON.stringify(selected.input_schema, null, 2)}</pre>
                </details>
              )}

              <label>Arguments (JSON)</label>
              <textarea
                value={args}
                onChange={(e) => setArgs(e.target.value)}
                rows={4}
              />
              <button onClick={handleExecute} disabled={loading}>
                Execute
              </button>

              {result && (
                <div className={`result ${result.error ? "error" : ""}`}>
                  <pre>{JSON.stringify(result, null, 2)}</pre>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
