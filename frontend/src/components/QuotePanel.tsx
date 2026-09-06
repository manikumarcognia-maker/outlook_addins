import { useState } from "react";
import type { EmailContext, ProposedQuote, QuoteRequest } from "../types";
import { approveQuote, parseQuoteFromEmail, proposeQuote } from "../services/quoteService";
import { Badge, ErrorBanner, LoadingState } from "./shared/UiPrimitives";

type QuoteState = "form" | "loading" | "review" | "editing" | "success" | "rejected" | "error";

const EMPTY_FORM: QuoteRequest = {
  customer: "",
  contact: "",
  pol: "",
  pod: "",
  cargo: "",
  commodity: "",
  weight: "",
};

interface QuotePanelProps {
  email: EmailContext | null;
  emailError: string | null;
}

export function QuotePanel({ email, emailError }: QuotePanelProps) {
  const [state, setState] = useState<QuoteState>("form");
  const [form, setForm] = useState<QuoteRequest>(EMPTY_FORM);
  const [quote, setQuote] = useState<ProposedQuote | null>(null);
  const [quoteId, setQuoteId] = useState("");
  const [error, setError] = useState<string | null>(null);

  function updateForm(field: keyof QuoteRequest, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleParseFromEmail() {
    if (!email) return;
    setState("loading");
    setError(null);
    try {
      const proposed = await parseQuoteFromEmail(email);
      setQuote(proposed);
      setForm({
        customer: proposed.customer,
        contact: proposed.contact,
        pol: proposed.pol,
        pod: proposed.pod,
        cargo: proposed.cargo,
        commodity: proposed.commodity,
        weight: "",
      });
      setState("review");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to parse email.");
      setState("error");
    }
  }

  async function handleManualPropose() {
    setState("loading");
    setError(null);
    try {
      const proposed = await proposeQuote(form);
      setQuote(proposed);
      setState("review");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to build quote.");
      setState("error");
    }
  }

  async function handleApprove() {
    if (!quote) return;
    setState("loading");
    setError(null);
    try {
      const result = await approveQuote(quote);
      setQuoteId(result.quoteId);
      setState("success");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create quote.");
      setState("error");
    }
  }

  function handleReject() {
    setQuote(null);
    setState("rejected");
    setError(null);
  }

  function handleReset() {
    setForm(EMPTY_FORM);
    setQuote(null);
    setQuoteId("");
    setState("form");
    setError(null);
  }

  if (emailError) return <ErrorBanner message={emailError} />;

  return (
    <section id="panel-quote" role="tabpanel" className="panel active">
      <p className="section-label">Proposed quotation</p>
      {error && <ErrorBanner message={error} />}

      {state === "form" && (
        <div className="card">
          <p className="card-title">Quote details</p>
          <div className="field">
            <label htmlFor="q-customer">Customer</label>
            <input id="q-customer" value={form.customer} onChange={(e) => updateForm("customer", e.target.value)} />
          </div>
          <div className="field-grid">
            <div className="field">
              <label htmlFor="q-pol">Origin (POL)</label>
              <input id="q-pol" value={form.pol} onChange={(e) => updateForm("pol", e.target.value)} />
            </div>
            <div className="field">
              <label htmlFor="q-pod">Destination (POD)</label>
              <input id="q-pod" value={form.pod} onChange={(e) => updateForm("pod", e.target.value)} />
            </div>
            <div className="field">
              <label htmlFor="q-cargo">Cargo</label>
              <input id="q-cargo" value={form.cargo} onChange={(e) => updateForm("cargo", e.target.value)} />
            </div>
            <div className="field">
              <label htmlFor="q-weight">Weight</label>
              <input id="q-weight" value={form.weight} onChange={(e) => updateForm("weight", e.target.value)} />
            </div>
          </div>
          <div className="actions">
            <button type="button" className="btn btn-primary" onClick={handleParseFromEmail} disabled={!email} aria-label="Parse quote from email">
              Parse from email
            </button>
            <button type="button" className="btn btn-outline" onClick={handleManualPropose} aria-label="Build quote from form">
              Build quote
            </button>
          </div>
        </div>
      )}

      {state === "loading" && <LoadingState message="Building proposed quote…" />}

      {state === "review" && quote && (
        <>
          <div style={{ marginBottom: 10 }}><Badge variant="pending">Awaiting your approval</Badge></div>
          <div className="card">
            <p className="card-title">Quote summary</p>
            <div className="field-grid">
              <div className="field"><label>Customer</label><div className="value">{quote.customer}</div></div>
              <div className="field"><label>Contact</label><div className="value">{quote.contact}</div></div>
              <div className="field"><label>POL</label><div className="value">{quote.pol}</div></div>
              <div className="field"><label>POD</label><div className="value">{quote.pod}</div></div>
              <div className="field"><label>Cargo</label><div className="value">{quote.cargo}</div></div>
              <div className="field"><label>Commodity</label><div className="value">{quote.commodity}</div></div>
            </div>
            <table className="charges-table">
              <thead>
                <tr><th>Charge</th><th>Qty</th><th>Rate</th><th>Amount</th></tr>
              </thead>
              <tbody>
                {quote.charges.map((line) => (
                  <tr key={line.description}>
                    <td>{line.description}</td>
                    <td>{line.qty}</td>
                    <td>{line.rate}</td>
                    <td>{line.amount}</td>
                  </tr>
                ))}
                <tr className="total"><td colSpan={3}>Total sell</td><td>{quote.total}</td></tr>
              </tbody>
            </table>
            <p className="hint">Nothing is saved until you approve.</p>
            <div className="actions">
              <button type="button" className="btn btn-success" onClick={handleApprove} aria-label="Accept and create quote">Accept and create quote</button>
              <button type="button" className="btn btn-outline" onClick={() => setState("editing")} aria-label="Edit quote">Edit</button>
              <button type="button" className="btn btn-danger" onClick={handleReject} aria-label="Reject quote">Reject</button>
            </div>
          </div>
        </>
      )}

      {state === "editing" && (
        <div className="card">
          <p className="card-title">Edit quote before creating</p>
          <div className="field">
            <label htmlFor="eq-customer">Customer</label>
            <input id="eq-customer" value={form.customer} onChange={(e) => updateForm("customer", e.target.value)} />
          </div>
          <div className="field-grid">
            <div className="field">
              <label htmlFor="eq-pol">POL</label>
              <input id="eq-pol" value={form.pol} onChange={(e) => updateForm("pol", e.target.value)} />
            </div>
            <div className="field">
              <label htmlFor="eq-pod">POD</label>
              <input id="eq-pod" value={form.pod} onChange={(e) => updateForm("pod", e.target.value)} />
            </div>
          </div>
          <div className="actions">
            <button type="button" className="btn btn-success" onClick={handleManualPropose} aria-label="Save and create quote">Save and create quote</button>
            <button type="button" className="btn btn-outline" onClick={() => setState("review")} aria-label="Cancel edit">Cancel</button>
          </div>
        </div>
      )}

      {state === "success" && (
        <>
          <div className="success-banner">Quote {quoteId} created (mock)</div>
          <div className="card">
            <p className="hint">Convert to a job in Fr8Labs when the customer confirms.</p>
            <button type="button" className="btn btn-outline btn-block" onClick={handleReset}>Create another</button>
          </div>
        </>
      )}

      {state === "rejected" && (
        <div className="card">
          <p className="card-title">Quote discarded</p>
          <p className="hint">No changes were made in Fr8Labs.</p>
          <button type="button" className="btn btn-outline btn-block" onClick={handleReset}>Start over</button>
        </div>
      )}
    </section>
  );
}
