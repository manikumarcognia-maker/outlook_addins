import { apiPost } from "./apiClient";
import type { DraftReplyInput, DraftReplyResult } from "../types";

interface DraftReplyApiResponse {
  draft: string;
  citations: Array<{
    document_id: string;
    original_filename: string;
    chunk_index: number;
  }>;
  rerank_succeeded: boolean;
}

const DRAFT_REPLY_TIMEOUT_MS = 3 * 60 * 1000;

export async function generateDraftReply(input: DraftReplyInput): Promise<DraftReplyResult> {
  console.info("[draftReply] request", {
    subject: input.subject,
    bodyChars: input.body.length,
    sender: input.senderEmail,
  });

  const response = await apiPost<DraftReplyApiResponse>(
    "/api/draft-reply",
    {
      subject: input.subject,
      body: input.body,
      sender_email: input.senderEmail,
      sender_name: input.senderName,
    },
    DRAFT_REPLY_TIMEOUT_MS
  );

  console.info("[draftReply] response", {
    draftChars: response.draft.length,
    citations: response.citations.length,
    rerankSucceeded: response.rerank_succeeded,
  });

  return { draft: response.draft };
}
