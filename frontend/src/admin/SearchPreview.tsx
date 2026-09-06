import { useState } from "react";
import { searchPreview } from "../services/adminDocumentService";
import type { SearchPreviewResult } from "../types";
import { ErrorBanner, LoadingState } from "../components/shared/UiPrimitives";

export function SearchPreview() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchPreviewResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  async function handleSearch() {
    if (!query.trim()) {
      setError("Enter a search query.");
      return;
    }

    setLoading(true);
    setError(null);
    setSearched(true);

    try {
      const items = await searchPreview(query.trim());
      setResults(items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed.");
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <h2 className="card-title">Quick Search Preview</h2>
      <p className="hint">Verify indexed content is retrievable without using the Outlook add-in.</p>

      {error && <ErrorBanner message={error} />}

      <div className="field">
        <label htmlFor="search-query">Search query</label>
        <input
          id="search-query"
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. transit time Singapore"
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
        />
      </div>

      <div className="actions">
        <button type="button" className="btn btn-primary" disabled={loading} onClick={handleSearch}>
          Search
        </button>
      </div>

      {loading && <LoadingState message="Searching…" />}

      {!loading && searched && results.length === 0 && !error && (
        <p className="hint">No results found for active documents.</p>
      )}

      {!loading &&
        results.map((item, index) => (
          <div key={`${item.document_id}-${item.chunk_index}-${index}`} className="search-result">
            <div className="search-result-meta">
              {item.original_filename} · chunk {item.chunk_index} ·{" "}
              <span className="mono">{item.document_id}</span>
            </div>
            <div className="search-result-snippet">{item.snippet}</div>
          </div>
        ))}
    </div>
  );
}
