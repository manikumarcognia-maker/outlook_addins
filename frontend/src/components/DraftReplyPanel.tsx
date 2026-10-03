import { useRef, useState } from "react";
import type { EmailContext } from "../types";
import { generateThreadAgentDraft } from "../services/emailAgentService";
import { fetchConversationMessages } from "../services/conversationMessages";
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
  const [citations, setCitations] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const inFlightRef = useRef(false);

  async function handleGenerate() {
    if (!email || state === "loading" || inFlightRef.current) return;
    inFlightRef.current = true;
    setState("loading");
    setError(null);
    try {
      let conversationMessages;
      let graphWarning: string | null = null;
      try {
        conversationMessages = await fetchConversationMessages(email.threadId);
      } catch (graphError) {
        graphWarning =
          graphError instanceof Error
            ? graphError.message
            : "Could not load full conversation from Microsoft Graph.";
        conversationMessages = [
          {
            sourceMessageId: email.sourceMessageId,
            body: email.body,
          },
        ];
      }

      const triggerInList = conversationMessages.some(
        (m) => m.sourceMessageId === email.sourceMessageId
      );
      if (!triggerInList) {
        conversationMessages = [
          ...conversationMessages,
          {
            sourceMessageId: email.sourceMessageId,
            body: email.body,
          },
        ];
      }

      const result = await generateThreadAgentDraft({
        threadId: email.threadId,
        emailBody: email.body,
        sourceMessageId: email.sourceMessageId,
        conversationMessages,
      });

      if (graphWarning) {
        setError(`Full thread sync unavailable: ${graphWarning} Only the open email was synced.`);
      }
      if (!result.draft.trim()) {
        throw new Error("The AI returned an empty draft. Please try again.");
      }
      setDraft(result.draft);
      setCitations(
        result.citations.map(
          (c) => `${c.originalFilename} (chunk ${c.chunkIndex})`
        )
      );
      setState("ready");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate draft.");
      setState("error");
    } finally {
      inFlightRef.current = false;
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
    setCitations([]);
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
            {citations.length > 0 && (
              <p className="hint" style={{ marginBottom: 8 }}>
                Sources: {citations.join("; ")}
              </p>
            )}
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
