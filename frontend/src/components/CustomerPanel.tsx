import { useEffect, useState } from "react";
import type { CustomerCreateInput, CustomerLookupResult, EmailContext } from "../types";
import { createCustomer, lookupCustomer } from "../services/customerService";
import { Badge, ErrorBanner, LoadingState } from "./shared/UiPrimitives";

type CustomerState = "loading" | "found" | "not_found" | "creating" | "created" | "error";

interface CustomerPanelProps {
  email: EmailContext | null;
  emailError: string | null;
}

export function CustomerPanel({ email, emailError }: CustomerPanelProps) {
  const [state, setState] = useState<CustomerState>("loading");
  const [lookup, setLookup] = useState<CustomerLookupResult | null>(null);
  const [form, setForm] = useState<CustomerCreateInput>({
    companyName: "",
    contactName: "",
    email: "",
    billingAddress: "",
  });
  const [customerId, setCustomerId] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!email || emailError) return;

    let cancelled = false;

    async function runLookup() {
      setState("loading");
      setError(null);
      try {
        const result = await lookupCustomer({
          email: email!.senderEmail,
          domain: email!.senderDomain,
          displayName: email!.senderName,
        });
        if (cancelled) return;
        setLookup(result);
        if (result.status === "found") {
          setState("found");
        } else {
          setForm(result.suggested);
          setState("not_found");
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Customer lookup failed.");
          setState("error");
        }
      }
    }

    runLookup();
    return () => {
      cancelled = true;
    };
  }, [email, emailError]);

  async function handleCreate() {
    setState("creating");
    setError(null);
    try {
      const result = await createCustomer(form);
      setCustomerId(result.customerId);
      setState("created");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create customer.");
      setState("error");
    }
  }

  if (emailError) return <ErrorBanner message={emailError} />;

  return (
    <section id="panel-customer" role="tabpanel" className="panel active">
      <p className="section-label">Sender lookup</p>
      {error && <ErrorBanner message={error} />}

      {state === "loading" && <LoadingState message="Looking up customer in Fr8Labs…" />}
      {state === "creating" && <LoadingState message="Creating customer…" />}

      {state === "found" && lookup?.status === "found" && (
        <>
          <div style={{ marginBottom: 10 }}><Badge variant="ready">Customer found</Badge></div>
          <div className="card">
            <p className="card-title">{lookup.profile.name}</p>
            <div className="profile-row"><span>Status</span><strong>{lookup.profile.status}</strong></div>
            <div className="profile-row"><span>Account code</span><strong>{lookup.profile.accountCode}</strong></div>
            <div className="profile-row"><span>Credit limit</span><strong>{lookup.profile.creditLimit}</strong></div>
            <div className="profile-row"><span>Recent shipment</span><strong>{lookup.profile.recentShipment}</strong></div>
            <div className="profile-row"><span>Open quotes</span><strong>{lookup.profile.openQuotes}</strong></div>
          </div>
          <p className="hint">Switch to Create Quote to build a new quotation for this customer.</p>
        </>
      )}

      {(state === "not_found" || state === "created") && (
        <>
          {state === "not_found" && (
            <div style={{ marginBottom: 10 }}><Badge variant="missing">Not in Fr8Labs</Badge></div>
          )}
          {state === "created" && (
            <div className="success-banner">Customer {customerId} created (mock)</div>
          )}
          <div className="card">
            <p className="card-title">{state === "created" ? "Customer saved" : "Create new customer"}</p>
            {state === "not_found" && (
              <p className="hint">Pre-filled from email. Review before saving.</p>
            )}
            <div className="field">
              <label htmlFor="c-company">Company name</label>
              <input
                id="c-company"
                value={form.companyName}
                onChange={(e) => setForm((f) => ({ ...f, companyName: e.target.value }))}
                disabled={state === "created"}
              />
            </div>
            <div className="field-grid">
              <div className="field">
                <label htmlFor="c-contact">Primary contact</label>
                <input
                  id="c-contact"
                  value={form.contactName}
                  onChange={(e) => setForm((f) => ({ ...f, contactName: e.target.value }))}
                  disabled={state === "created"}
                />
              </div>
              <div className="field">
                <label htmlFor="c-email">Email</label>
                <input
                  id="c-email"
                  value={form.email}
                  onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                  disabled={state === "created"}
                />
              </div>
              <div className="field full">
                <label htmlFor="c-address">Billing address</label>
                <input
                  id="c-address"
                  value={form.billingAddress}
                  onChange={(e) => setForm((f) => ({ ...f, billingAddress: e.target.value }))}
                  disabled={state === "created"}
                />
              </div>
            </div>
            {state === "not_found" && (
              <div className="actions">
                <button type="button" className="btn btn-success" onClick={handleCreate} aria-label="Create customer">
                  Create customer
                </button>
                <button type="button" className="btn btn-outline" aria-label="Open in Fr8Labs">
                  Open in Fr8Labs
                </button>
              </div>
            )}
            <p className="hint">Partner API pending — placeholder until Fr8Labs docs arrive.</p>
          </div>
        </>
      )}
    </section>
  );
}
