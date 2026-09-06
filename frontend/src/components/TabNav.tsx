import type { PanelView } from "../types";

const TABS: { id: PanelView; label: string; short: string }[] = [
  { id: "draft", label: "Draft Reply", short: "Reply" },
  { id: "quote", label: "Create Quote", short: "Quote" },
  { id: "customer", label: "Customer", short: "Customer" },
];

interface TabNavProps {
  active: PanelView;
  onChange: (view: PanelView) => void;
}

export function TabNav({ active, onChange }: TabNavProps) {
  return (
    <nav className="tab-nav" role="tablist" aria-label="Fr8Labs actions">
      {TABS.map((tab) => (
        <button
          key={tab.id}
          type="button"
          role="tab"
          aria-selected={active === tab.id}
          aria-controls={`panel-${tab.id}`}
          className={`tab-btn ${active === tab.id ? "active" : ""}`}
          onClick={() => onChange(tab.id)}
        >
          <span className="tab-short" aria-hidden="true">{tab.short}</span>
          {tab.label}
        </button>
      ))}
    </nav>
  );
}
