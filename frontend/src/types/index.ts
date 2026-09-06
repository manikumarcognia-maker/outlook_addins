export type PanelView = "draft" | "quote" | "customer";

export interface EmailContext {
  subject: string;
  body: string;
  senderEmail: string;
  senderName: string;
  senderDomain: string;
}

export interface DraftReplyInput {
  subject: string;
  body: string;
  senderEmail: string;
  senderName: string;
}

export interface DraftReplyResult {
  draft: string;
}

export interface QuoteRequest {
  customer: string;
  contact: string;
  pol: string;
  pod: string;
  cargo: string;
  commodity: string;
  weight: string;
}

export interface ChargeLine {
  description: string;
  qty: number;
  rate: string;
  amount: string;
}

export interface ProposedQuote {
  customer: string;
  contact: string;
  pol: string;
  pod: string;
  cargo: string;
  commodity: string;
  charges: ChargeLine[];
  total: string;
}

export interface QuoteApproveResult {
  quoteId: string;
}

export interface CustomerLookupInput {
  email: string;
  domain: string;
  displayName: string;
}

export interface CustomerProfile {
  name: string;
  status: string;
  accountCode: string;
  creditLimit: string;
  recentShipment: string;
  openQuotes: string;
}

export interface CustomerSuggestedFields {
  companyName: string;
  contactName: string;
  email: string;
  billingAddress: string;
}

export type CustomerLookupResult =
  | { status: "found"; profile: CustomerProfile }
  | { status: "not_found"; suggested: CustomerSuggestedFields };

export interface CustomerCreateInput {
  companyName: string;
  contactName: string;
  email: string;
  billingAddress: string;
}

export interface CustomerCreateResult {
  customerId: string;
}

export interface IndexedDocument {
  document_id: string;
  original_filename: string | null;
  content_hash: string | null;
  uploaded_at: string | null;
  active: boolean | null;
  chunk_count: number;
}

export interface UploadResult {
  document_id: string;
  chunk_count: number;
  original_filename: string;
}

export interface SearchPreviewResult {
  document_id: string;
  original_filename: string;
  chunk_index: number;
  snippet: string;
}
