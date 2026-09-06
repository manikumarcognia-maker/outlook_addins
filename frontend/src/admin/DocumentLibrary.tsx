import { useCallback, useEffect, useState } from "react";
import { listDocuments, supersedeDocument } from "../services/adminDocumentService";
import type { IndexedDocument } from "../types";
import { Badge, ErrorBanner, LoadingState } from "../components/shared/UiPrimitives";

interface DocumentLibraryProps {
  refreshKey: number;
}

export function DocumentLibrary({ refreshKey }: DocumentLibraryProps) {
  const [documents, setDocuments] = useState<IndexedDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [supersedingId, setSupersedingId] = useState<string | null>(null);

  const loadDocuments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const docs = await listDocuments();
      setDocuments(docs);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load documents.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments, refreshKey]);

  async function handleSupersede(documentId: string) {
    setSupersedingId(documentId);
    setError(null);
    try {
      await supersedeDocument(documentId);
      await loadDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to supersede document.");
    } finally {
      setSupersedingId(null);
    }
  }

  function formatDate(iso: string | null): string {
    if (!iso) return "—";
    try {
      return new Date(iso).toLocaleString();
    } catch {
      return iso;
    }
  }

  return (
    <div className="card">
      <h2 className="card-title">Document Library</h2>

      {error && <ErrorBanner message={error} />}

      {loading ? (
        <LoadingState message="Loading documents…" />
      ) : documents.length === 0 ? (
        <p className="hint">No documents indexed yet.</p>
      ) : (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Filename</th>
                <th>Document ID</th>
                <th>Uploaded</th>
                <th>Status</th>
                <th>Chunks</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => {
                const isActive = doc.active !== false;
                return (
                  <tr key={doc.document_id} className={isActive ? "" : "row-inactive"}>
                    <td>{doc.original_filename ?? "—"}</td>
                    <td className="mono">{doc.document_id}</td>
                    <td>{formatDate(doc.uploaded_at)}</td>
                    <td>
                      <Badge variant={isActive ? "ready" : "missing"}>
                        {isActive ? "Active" : "Superseded"}
                      </Badge>
                    </td>
                    <td>{doc.chunk_count}</td>
                    <td>
                      {isActive && (
                        <button
                          type="button"
                          className="btn btn-danger"
                          disabled={supersedingId === doc.document_id}
                          onClick={() => handleSupersede(doc.document_id)}
                        >
                          {supersedingId === doc.document_id ? "Superseding…" : "Mark Superseded"}
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
