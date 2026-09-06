import { useState } from "react";
import type { PanelView } from "./types";
import { useEmailItem } from "./hooks/useEmailItem";
import { AppHeader } from "./components/AppHeader";
import { TabNav } from "./components/TabNav";
import { DraftReplyPanel } from "./components/DraftReplyPanel";
import { QuotePanel } from "./components/QuotePanel";
import { CustomerPanel } from "./components/CustomerPanel";
import { LoadingState } from "./components/shared/UiPrimitives";

function getInitialView(): PanelView {
  const view = new URLSearchParams(window.location.search).get("view");
  if (view === "draft" || view === "quote" || view === "customer") return view;
  return "draft";
}

export default function App() {
  const [activeView, setActiveView] = useState<PanelView>(getInitialView);
  const { email, loading, error } = useEmailItem();

  return (
    <div className="app">
      <AppHeader />
      <TabNav active={activeView} onChange={setActiveView} />

      {loading ? (
        <LoadingState message="Reading open email…" />
      ) : (
        <>
          {activeView === "draft" && (
            <DraftReplyPanel email={email} emailError={error} />
          )}
          {activeView === "quote" && (
            <QuotePanel email={email} emailError={error} />
          )}
          {activeView === "customer" && (
            <CustomerPanel email={email} emailError={error} />
          )}
        </>
      )}
    </div>
  );
}
