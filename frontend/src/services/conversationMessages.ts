import { getAccessToken } from "../auth";
import { sanitizeText, truncateText } from "../utils/sanitize";

export interface ConversationMessagePayload {
  sourceMessageId: string;
  body: string;
  receivedAt?: string;
}

interface GraphMessage {
  id?: string;
  internetMessageId?: string;
  receivedDateTime?: string;
  isDraft?: boolean;
  from?: { emailAddress?: { address?: string } };
  body?: { contentType?: string; content?: string };
}

interface GraphListResponse {
  value?: GraphMessage[];
  "@odata.nextLink"?: string;
}

const GRAPH_BASE = "https://graph.microsoft.com/v1.0";

function escapeODataLiteral(value: string): string {
  return value.replace(/'/g, "''");
}

function messageSourceId(message: GraphMessage): string {
  const internet = message.internetMessageId?.trim();
  if (internet) return internet;
  const id = message.id?.trim();
  if (id) return id;
  throw new Error("Graph message missing internetMessageId and id.");
}

function messageBodyText(message: GraphMessage): string {
  const raw = message.body?.content ?? "";
  if (message.body?.contentType === "html") {
    return truncateText(sanitizeText(raw));
  }
  return truncateText(sanitizeText(raw));
}

function mailboxUserEmail(): string {
  const profile = Office.context.mailbox.userProfile;
  return (profile?.emailAddress || "").trim().toLowerCase();
}

function isCustomerMessage(message: GraphMessage, userEmail: string): boolean {
  if (message.isDraft) return false;
  const from = message.from?.emailAddress?.address?.trim().toLowerCase() || "";
  if (!from) return true;
  if (!userEmail) return true;
  return from !== userEmail;
}

async function fetchGraphJson<T>(url: string, token: string): Promise<T> {
  const response = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      `Microsoft Graph request failed (${response.status}): ${detail.slice(0, 200)}`
    );
  }
  return (await response.json()) as T;
}

export async function fetchConversationMessages(
  conversationId: string
): Promise<ConversationMessagePayload[]> {
  const trimmed = conversationId.trim();
  if (!trimmed) {
    throw new Error("conversationId is required to load the thread.");
  }

  const token = await getAccessToken();
  if (!token || token === "mock-token-for-dev") {
    throw new Error(
      "Microsoft sign-in is not configured. Set up Entra SSO (WebApplicationInfo) and Mail.Read."
    );
  }

  const userEmail = mailboxUserEmail();
  const filter = `conversationId eq '${escapeODataLiteral(trimmed)}'`;
  let url =
    `${GRAPH_BASE}/me/messages?$filter=${encodeURIComponent(filter)}` +
    "&$select=internetMessageId,id,receivedDateTime,body,from,isDraft" +
    "&$orderby=receivedDateTime asc&$top=50";

  const messages: ConversationMessagePayload[] = [];

  while (url) {
    const page = await fetchGraphJson<GraphListResponse>(url, token);
    for (const item of page.value ?? []) {
      if (!isCustomerMessage(item, userEmail)) continue;
      const body = messageBodyText(item);
      if (!body.trim()) continue;
      messages.push({
        sourceMessageId: messageSourceId(item),
        body,
        receivedAt: item.receivedDateTime,
      });
    }
    url = page["@odata.nextLink"] ?? "";
  }

  if (messages.length === 0) {
    throw new Error("No customer messages found for this conversation in Graph.");
  }

  return messages;
}
