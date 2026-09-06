import { useEffect, useState } from "react";
import { getSupportedTypes, uploadDocument } from "../services/adminDocumentService";
import type { UploadResult } from "../types";
import { ErrorBanner, LoadingState } from "../components/shared/UiPrimitives";

interface UploadSectionProps {
  onIndexed: () => void;
}

export function UploadSection({ onIndexed }: UploadSectionProps) {
  const [supportedTypes, setSupportedTypes] = useState<string[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<UploadResult | null>(null);

  useEffect(() => {
    getSupportedTypes()
      .then(setSupportedTypes)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load supported types."));
  }, []);

  const accept = supportedTypes.join(",");

  async function handleSubmit() {
    if (!file) {
      setError("Please select a file to upload.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const uploadResult = await uploadDocument(file);
      setResult(uploadResult);
      setFile(null);
      onIndexed();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <h2 className="card-title">Upload &amp; Index</h2>

      {error && <ErrorBanner message={error} />}

      {loading ? (
        <LoadingState message="Indexing document… This may take a minute or two for longer documents due to embedding rate limits." />
      ) : (
        <>
          <div className="field">
            <label htmlFor="upload-file">Document file</label>
            <input
              id="upload-file"
              type="file"
              accept={accept || ".pdf,.docx,.txt"}
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
            {supportedTypes.length > 0 && (
              <p className="hint">Supported: {supportedTypes.join(", ")}</p>
            )}
          </div>

          <div className="actions">
            <button
              type="button"
              className="btn btn-primary"
              disabled={!file}
              onClick={handleSubmit}
            >
              Index Document
            </button>
          </div>

          {result && (
            <div className="upload-success" role="status">
              <div>Indexed successfully.</div>
              <div className="mono">document_id: {result.document_id}</div>
              <div>Chunks: {result.chunk_count}</div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
