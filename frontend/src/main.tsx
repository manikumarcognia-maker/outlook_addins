import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles/taskpane.css";

function renderApp() {
  const root = document.getElementById("root");
  if (!root) return;

  createRoot(root).render(
    <StrictMode>
      <App />
    </StrictMode>
  );
}

function showBootError(message: string) {
  const root = document.getElementById("root");
  if (!root) return;
  root.innerHTML = `<p style="margin:16px;font-family:Segoe UI,sans-serif;color:#b42318">${message}</p>`;
}

if (typeof Office !== "undefined") {
  Office.onReady((info) => {
    if (info.host === Office.HostType.Outlook) {
      renderApp();
      return;
    }
    showBootError("This add-in only runs in Outlook.");
  });
} else {
  // Local browser preview (not inside Outlook).
  renderApp();
}
