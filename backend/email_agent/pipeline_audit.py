"""Structured NDJSON audit records for each inbound pipeline step."""

from __future__ import annotations

from typing import Any

from email_agent import audit_log
from email_agent.coordinator import RefinementResult
from email_agent.facts import ExtractionResult
from email_agent.models import ThreadState
from email_agent.retrieval import RetrievalResult, RetrievedChunk
from email_agent.synthesis import SynthesisResult
from email_agent.conversation import ThreadSyncResult

AUDIT_EMAIL_PREVIEW_CHARS = 500
AUDIT_CHUNK_CONTENT_CHARS = 400
AUDIT_DRAFT_PREVIEW_CHARS = 1200
AUDIT_SUMMARY_CHARS = 2000


def _clip(text: str, max_len: int) -> str:
    stripped = text.strip()
    if len(stripped) <= max_len:
        return stripped
    return stripped[: max_len - 3] + "..."


def _chunks_payload(chunks: list[RetrievedChunk]) -> list[dict[str, Any]]:
    return [
        {
            "document_id": chunk["document_id"],
            "original_filename": chunk["original_filename"],
            "chunk_index": chunk["chunk_index"],
            "content_preview": _clip(chunk.get("content", ""), AUDIT_CHUNK_CONTENT_CHARS),
            "content_chars": len(chunk.get("content", "")),
        }
        for chunk in chunks
    ]


def audit_pipeline_thread_sync(
    *,
    thread_id: str,
    trigger_source_message_id: str,
    sync_result: ThreadSyncResult,
) -> None:
    audit_log.audit_event(
        "pipeline_thread_sync",
        thread_id=thread_id,
        trigger_source_message_id=trigger_source_message_id,
        synced_count=sync_result.synced_count,
        skipped_count=sync_result.skipped_count,
        synced_source_message_ids=sync_result.synced_source_message_ids[:20],
    )


def audit_pipeline_extraction(
    *,
    thread_id: str,
    source_message_id: str,
    email_preview: str,
    extraction: ExtractionResult,
) -> None:
    audit_log.audit_event(
        "pipeline_extraction",
        thread_id=thread_id,
        source_message_id=source_message_id,
        email_preview=_clip(email_preview, AUDIT_EMAIL_PREVIEW_CHARS),
        email_chars=len(email_preview),
        subject_id=extraction.subject_id,
        facts=extraction.facts,
        open_questions=extraction.open_questions,
    )


def audit_pipeline_thread_persisted(
    *,
    thread_id: str,
    state: ThreadState,
) -> None:
    audit_log.audit_event(
        "pipeline_thread_persisted",
        thread_id=thread_id,
        facts_by_subject=state.facts,
        summary=_clip(state.summary or "", AUDIT_SUMMARY_CHARS),
        summary_chars=len(state.summary or ""),
        unsummarized_messages=[
            {"role": m.role, "body_preview": _clip(m.body, 200), "id": m.id}
            for m in state.recent_messages
        ],
    )


def audit_pipeline_refine(
    *,
    thread_id: str,
    refined: RefinementResult,
) -> None:
    audit_log.audit_event(
        "pipeline_refine",
        thread_id=thread_id,
        search_query=refined.query,
        search_filters=refined.filters,
    )


def audit_pipeline_synthesis(
    *,
    thread_id: str,
    synthesis: SynthesisResult,
) -> None:
    audit_log.audit_event(
        "pipeline_synthesis",
        thread_id=thread_id,
        retrieval_status=synthesis.retrieval_status,
        retrieval_message=synthesis.retrieval_message,
        draft_preview=_clip(synthesis.draft_text, AUDIT_DRAFT_PREVIEW_CHARS),
        draft_chars=len(synthesis.draft_text),
        citations=[
            {
                "document_id": c.document_id,
                "original_filename": c.original_filename,
                "chunk_index": c.chunk_index,
            }
            for c in synthesis.citations
        ],
    )


def audit_pipeline_retrieval(
    *,
    thread_id: str,
    search_query: str,
    retrieval_result: RetrievalResult,
) -> None:
    status = retrieval_result["status"]
    fields: dict[str, Any] = {
        "thread_id": thread_id,
        "search_query": search_query,
        "retrieval_status": status,
    }
    if status == "error":
        fields["failure_type"] = retrieval_result.get("failureType")
        partial = retrieval_result.get("partialResults") or []
        fields["partial_chunk_count"] = len(partial)
        fields["chunks"] = _chunks_payload(list(partial))
    else:
        chunks = list(retrieval_result.get("results") or [])
        fields["chunk_count"] = len(chunks)
        fields["chunks"] = _chunks_payload(chunks)
        if not chunks:
            fields["empty_message"] = retrieval_result.get("message")
    audit_log.audit_event("pipeline_retrieval", **fields)
