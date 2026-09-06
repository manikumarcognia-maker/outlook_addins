import { useState } from "react";
import type { EmailContext } from "../types";
import { generateDraftReply } from "../services/draftReplyService";
import { insertDraftIntoReply } from "../hooks/useEmailItem";
import { Badge, ErrorBanner, LoadingState } from "./shared/UiPrimitives";

type DraftState = "idle" | "loading" | "ready" | "error" | "inserted";

interface DraftReplyPanelProps {
  email: EmailContext | null;
  emailError: string | null;
}

export function DraftReplyPanel({ email, emailError }: DraftReplyPanelProps) {
  const [state, setState] = useState<DraftState>("idle");
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    if (!email) return;
    setState("loading");
    setError(null);
    try {
      const result = await generateDraftReply({
        subject: email.subject,
        body: email.body,
        senderEmail: email.senderEmail,
        senderName: email.senderName,
      });
      if (!result.draft.trim()) {
        throw new Error("The AI returned an empty draft. Please try again.");
      }
      setDraft(result.draft);
      setState("ready");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate draft.");
      setState("error");
    }
  }

  async function handleInsert() {
    setError(null);
    try {
      await insertDraftIntoReply(draft);
      setState("inserted");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to open reply form.");
      setState("error");
    }
  }

  function handleDiscard() {
    setDraft("");
    setState("idle");
    setError(null);
  }

  if (emailError) return <ErrorBanner message={emailError} />;

  return (
    <section id="panel-draft" role="tabpanel" aria-labelledby="tab-draft" className="panel active">
      <p className="section-label">AI draft reply</p>

      {error && <ErrorBanner message={error} />}

      {state === "error" && (
        <div className="card">
          <p className="card-title">Something went wrong</p>
          <div className="actions">
            <button type="button" className="btn btn-primary" onClick={() => { setState("idle"); setError(null); }} aria-label="Try again">
              Try again
            </button>
          </div>
        </div>
      )}

      {state === "idle" && (
        <div className="card">
          <p className="card-title">Generate a reply to this email</p>
          <p className="hint">
            AI reads the open email and drafts a professional reply. Nothing is sent until you click Send in Outlook.
          </p>
          <div className="actions">
            <button
              type="button"
              className="btn btn-primary btn-block"
              onClick={handleGenerate}
              disabled={!email}
              aria-label="Generate AI draft reply"
            >
              Generate draft
            </button>
          </div>
        </div>
      )}

      {state === "loading" && <LoadingState message="Reading email and drafting reply…" />}

      {(state === "ready" || state === "inserted") && (
        <>
          <div style={{ marginBottom: 10 }}>
            <Badge variant={state === "inserted" ? "ready" : "draft"}>
              {state === "inserted" ? "Inserted into reply" : "Draft ready"}
            </Badge>
          </div>
          <div className="card">
            <p className="card-title">Suggested reply</p>
            <div className="field">
              <label htmlFor="draft-text">Edit before inserting</label>
              <textarea
                id="draft-text"
                rows={14}
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                aria-label="Draft reply text"
              />
            </div>
            <div className="actions">
              <button
                type="button"
                className="btn btn-success"
                onClick={handleInsert}
                disabled={state === "inserted"}
                aria-label="Insert draft into Outlook reply"
              >
                Insert into reply
              </button>
              <button type="button" className="btn btn-outline" onClick={handleGenerate} aria-label="Regenerate draft">
                Regenerate
              </button>
              <button type="button" className="btn btn-outline" onClick={handleDiscard} aria-label="Discard draft">
                Discard
              </button>
            </div>
          </div>
        </>
      )}
    </section>
  );
}
