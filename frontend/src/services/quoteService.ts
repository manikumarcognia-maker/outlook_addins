import { getAccessToken } from "../auth";
import type {
  EmailContext,
  ProposedQuote,
  QuoteApproveResult,
  QuoteRequest,
} from "../types";
import { delay } from "../utils/officeReady";

/**
 * MOCK — swap for fetch('https://your-backend/create-quote', ...) later.
 */
export async function parseQuoteFromEmail(email: EmailContext): Promise<ProposedQuote> {
  await getAccessToken();
  await delay(1100);

  const customer = email.senderName || email.senderDomain || "Unknown customer";

  return {
    customer,
    contact: email.senderEmail || "",
    pol: "SGSIN — Singapore",
    pod: "USLAX — Los Angeles",
    cargo: "Ocean FCL · 2×40HC",
    commodity: "General cargo",
    charges: [
      { description: "Ocean freight", qty: 2, rate: "USD 1,200", amount: "USD 2,400" },
      { description: "THC origin", qty: 2, rate: "USD 180", amount: "USD 360" },
      { description: "Documentation", qty: 1, rate: "USD 35", amount: "USD 35" },
    ],
    total: "USD 2,795",
  };
}

export async function proposeQuote(request: QuoteRequest): Promise<ProposedQuote> {
  await getAccessToken();
  await delay(900);

  return {
    customer: request.customer,
    contact: request.contact,
    pol: request.pol,
    pod: request.pod,
    cargo: request.cargo,
    commodity: request.commodity,
    charges: [
      { description: "Ocean freight", qty: 1, rate: "USD 1,200", amount: "USD 1,200" },
      { description: "THC origin", qty: 1, rate: "USD 180", amount: "USD 180" },
    ],
    total: "USD 1,380",
  };
}

export async function approveQuote(_quote: ProposedQuote): Promise<QuoteApproveResult> {
  await getAccessToken();
  await delay(800);
  return { quoteId: "QT-2026-0142" };
}
