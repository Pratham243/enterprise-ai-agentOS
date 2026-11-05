import { useState } from "react";
import { api } from "../services/api";

export default function Documents() {
  const [text, setText] = useState("");
  const [source, setSource] = useState("");
  const [ingestResult, setIngestResult] = useState(null);

  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleIngest = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    setLoading(true);
    try {
      const data = await api.ragIngest(text, source || "manual");
      setIngestResult(data);
      setText("");
      setSource("");
    } catch (err) {
      setIngestResult({ error: err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    try {
      const data = await api.ragQuery(query);
      setSearchResults(data);
    } catch (err) {
      setSearchResults({ error: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <h2>Document Manager</h2>

      <div className="grid two-col">
        <div className="card">
          <h3>Ingest Document</h3>
          <form onSubmit={handleIngest}>
            <label>Source name</label>
            <input
              type="text"
              value={source}
              onChange={(e) => setSource(e.target.value)}
              placeholder="e.g. company-handbook"
            />
            <label>Document text</label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste document content here..."
              rows={6}
            />
            <button type="submit" disabled={loading || !text.trim()}>
              Ingest
            </button>
          </form>
          {ingestResult && (
            <div className={`result ${ingestResult.error ? "error" : ""}`}>
              <pre>{JSON.stringify(ingestResult, null, 2)}</pre>
            </div>
          )}
        </div>

        <div className="card">
          <h3>Search Documents</h3>
          <form onSubmit={handleSearch}>
            <label>Search query</label>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="What is the refund policy?"
            />
            <button type="submit" disabled={loading || !query.trim()}>
              Search
            </button>
          </form>
          {searchResults && (
            <div className={`result ${searchResults.error ? "error" : ""}`}>
              {searchResults.results ? (
                searchResults.results.map((r, i) => (
                  <div key={i} className="search-result">
                    <div className="search-score">
                      Score: {r.score?.toFixed(3)}
                    </div>
                    <p>{r.text}</p>
                  </div>
                ))
              ) : (
                <pre>{JSON.stringify(searchResults, null, 2)}</pre>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
