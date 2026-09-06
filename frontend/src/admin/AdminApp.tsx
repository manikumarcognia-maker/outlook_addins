import { useCallback, useState } from "react";
import { DocumentLibrary } from "./DocumentLibrary";
import { SearchPreview } from "./SearchPreview";
import { UploadSection } from "./UploadSection";

export default function AdminApp() {
  const [refreshKey, setRefreshKey] = useState(0);

  const handleIndexed = useCallback(() => {
    setRefreshKey((k) => k + 1);
  }, []);

  return (
    <div className="admin-app">
      <header className="app-header">
        <h1>Fr8Labs Document Admin</h1>
        <p className="sub">Upload, index, and manage RAG knowledge-base documents</p>
      </header>

      <main className="admin-content">
        <section className="admin-section">
          <UploadSection onIndexed={handleIndexed} />
        </section>

        <section className="admin-section">
          <DocumentLibrary refreshKey={refreshKey} />
        </section>

        <section className="admin-section">
          <SearchPreview />
        </section>
      </main>
    </div>
  );
}
