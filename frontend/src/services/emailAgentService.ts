import { apiGet, apiPost } from "./apiClient";
import type { EmailAgentDraftResult, EmailAgentInboundInput } from "../types";

const INBOUND_TIMEOUT_MS = 5 * 60 * 1000;

interface InboundApiResponse {
  draft_id: string;
  duplicate: boolean;
}

interface DraftApiResponse {
  id: string;
  thread_id: string;
  draft_body: string;
  retrieval_status: string;
  citations: Array<{
    document_id: string;
    original_filename: string;
    chunk_index: number;
  }>;
  status: string;
}

export async function generateThreadAgentDraft(
  input: EmailAgentInboundInput
): Promise<EmailAgentDraftResult> {
  console.info("[emailAgent] inbound", {
    threadId: input.threadId,
    bodyChars: input.emailBody.length,
    sourceMessageId: input.sourceMessageId,
    conversationCount: input.conversationMessages.length,
    duplicateCheck: true,
  });

  const inbound = await apiPost<InboundApiResponse>(
    "/api/email-agent/inbound",
    {
      thread_id: input.threadId,
      email_body: input.emailBody,
      source_message_id: input.sourceMessageId,
      conversation_messages: input.conversationMessages.map((message) => ({
        source_message_id: message.sourceMessageId,
        body: message.body,
        received_at: message.receivedAt ?? null,
      })),
    },
    INBOUND_TIMEOUT_MS
  );

  const draft = await apiGet<DraftApiResponse>(`/api/email-agent/drafts/${inbound.draft_id}`);

  console.info("[emailAgent] draft loaded", {
    draftId: draft.id,
    duplicate: inbound.duplicate,
    status: draft.status,
    citations: draft.citations.length,
  });

  return {
    draftId: draft.id,
    draft: draft.draft_body,
    duplicate: inbound.duplicate,
    retrievalStatus: draft.retrieval_status,
    citations: draft.citations.map((c) => ({
      documentId: c.document_id,
      originalFilename: c.original_filename,
      chunkIndex: c.chunk_index,
    })),
  };
}
