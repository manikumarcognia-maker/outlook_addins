"""Draft review queue: persist synthesis output, approve, send (no auto-send on inbound)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from psycopg.errors import UniqueViolation

from email_agent.audit_log import audit_event
from email_agent.messages import add_message_and_maybe_summarize
from email_agent.store import load_thread_state, persist_thread_state
from email_agent.synthesis import RetrievalStatus, SynthesisResult
from email_agent.validation import require_non_empty
from rag.models import Citation
from rag.pg_store import get_connection, warm_pg_runtime

logger = logging.getLogger("fr8labs.email_agent.drafts")

DraftReviewStatus = Literal["pending_review", "approved", "edited_and_approved"]


@dataclass(frozen=True)
class DraftRecord:
    id: str
    thread_id: str
    draft_body: str
    retrieval_status: RetrievalStatus
    citations: list[Citation]
    status: DraftReviewStatus
    created_at: datetime
    reviewed_at: datetime | None
    reviewed_by: str | None
    sent_at: datetime | None


def _citations_to_json(citations: list[Citation]) -> str:
    payload = [
        {
            "document_id": c.document_id,
            "original_filename": c.original_filename,
            "chunk_index": c.chunk_index,
        }
        for c in citations
    ]
    return json.dumps(payload)


def _citations_from_json(raw: Any) -> list[Citation]:
    if not isinstance(raw, list):
        return []
    out: list[Citation] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            out.append(
                Citation(
                    document_id=str(item.get("document_id", "")),
                    original_filename=str(item.get("original_filename", "")),
                    chunk_index=int(item.get("chunk_index", -1)),
                )
            )
        except (TypeError, ValueError) as exc:
            logger.debug("CITATION_JSON_SKIP | error=%s", exc)
            continue
    return out


def _row_to_record(row: dict[str, Any]) -> DraftRecord:
    return DraftRecord(
        id=str(row["id"]),
        thread_id=row["thread_id"],
        draft_body=row["draft_body"],
        retrieval_status=row["retrieval_status"],
        citations=_citations_from_json(row["citations"]),
        status=row["status"],
        created_at=row["created_at"],
        reviewed_at=row["reviewed_at"],
        reviewed_by=row["reviewed_by"],
        sent_at=row["sent_at"],
    )


def get_draft_id_for_message(thread_id: str, source_message_id: str) -> str | None:
    tid = require_non_empty(thread_id, "thread_id")
    mid = require_non_empty(source_message_id, "source_message_id")
    warm_pg_runtime()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id FROM drafts
                WHERE thread_id = %s AND source_message_id = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (tid, mid),
            )
            row = cur.fetchone()
    if row is None:
        return None
    return str(row["id"])


def save_draft_for_review(
    thread_id: str,
    synthesis: SynthesisResult,
    *,
    source_message_id: str | None = None,
) -> str:
    tid = require_non_empty(thread_id, "thread_id")
    body = synthesis.draft_text.strip()
    if not body:
        raise ValueError("synthesis.draft_text cannot be empty.")

    mid = source_message_id.strip() if source_message_id else None
    warm_pg_runtime()
    try:
        with get_connection() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT 1 FROM threads WHERE thread_id = %s",
                        (tid,),
                    )
                    if cur.fetchone() is None:
                        raise ValueError(f"Thread not found: {tid}")

                    cur.execute(
                        """
                        INSERT INTO drafts (
                          thread_id, draft_body, retrieval_status, citations, status,
                          source_message_id
                        ) VALUES (%s, %s, %s, %s::jsonb, 'pending_review', %s)
                        RETURNING id
                        """,
                        (
                            tid,
                            body,
                            synthesis.retrieval_status,
                            _citations_to_json(synthesis.citations),
                            mid,
                        ),
                    )
                    row = cur.fetchone()
                    if row is None:
                        raise RuntimeError("Failed to insert draft.")
                    draft_id = str(row["id"])
    except UniqueViolation:
        if mid:
            existing = get_draft_id_for_message(tid, mid)
            if existing is not None:
                logger.info(
                    "DRAFT_DEDUPE_RACE | thread_id=%s | source_message_id=%s | draft_id=%s",
                    tid,
                    mid,
                    existing,
                )
                return existing
        raise

    logger.info(
        "DRAFT_SAVED | draft_id=%s | thread_id=%s | retrieval_status=%s | citations=%s",
        draft_id,
        tid,
        synthesis.retrieval_status,
        len(synthesis.citations),
    )
    audit_event(
        "draft_saved",
        draft_id=draft_id,
        thread_id=tid,
        retrieval_status=synthesis.retrieval_status,
        source_message_id=source_message_id,
    )
    return draft_id


def get_draft(draft_id: str) -> DraftRecord:
    did = require_non_empty(draft_id, "draft_id")
    warm_pg_runtime()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                  id, thread_id, draft_body, retrieval_status, citations,
                  status, created_at, reviewed_at, reviewed_by, sent_at
                FROM drafts
                WHERE id = %s
                """,
                (did,),
            )
            row = cur.fetchone()
    if row is None:
        raise ValueError(f"Draft not found: {did}")
    return _row_to_record(row)


def list_pending_drafts(thread_id: str | None = None) -> list[DraftRecord]:
    warm_pg_runtime()
    with get_connection() as conn:
        with conn.cursor() as cur:
            if thread_id is not None:
                tid = require_non_empty(thread_id, "thread_id")
                cur.execute(
                    """
                    SELECT
                      id, thread_id, draft_body, retrieval_status, citations,
                      status, created_at, reviewed_at, reviewed_by, sent_at
                    FROM drafts
                    WHERE status = 'pending_review' AND thread_id = %s
                    ORDER BY created_at DESC
                    """,
                    (tid,),
                )
            else:
                cur.execute(
                    """
                    SELECT
                      id, thread_id, draft_body, retrieval_status, citations,
                      status, created_at, reviewed_at, reviewed_by, sent_at
                    FROM drafts
                    WHERE status = 'pending_review'
                    ORDER BY created_at DESC
                    """
                )
            rows = cur.fetchall()
    return [_row_to_record(row) for row in rows]


def approve_draft(
    draft_id: str,
    reviewed_by: str,
    draft_body: str | None = None,
) -> DraftRecord:
    did = require_non_empty(draft_id, "draft_id")
    reviewer = require_non_empty(reviewed_by, "reviewed_by")

    warm_pg_runtime()
    with get_connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT status FROM drafts WHERE id = %s",
                    (did,),
                )
                row = cur.fetchone()
                if row is None:
                    raise ValueError(f"Draft not found: {did}")
                if row["status"] != "pending_review":
                    raise ValueError(
                        f"Draft {did} is not pending review (status={row['status']!r})."
                    )

                if draft_body is not None:
                    new_body = draft_body.strip()
                    if not new_body:
                        raise ValueError("draft_body cannot be empty when provided.")
                    new_status = "edited_and_approved"
                    cur.execute(
                        """
                        UPDATE drafts
                        SET draft_body = %s,
                            status = %s,
                            reviewed_at = NOW(),
                            reviewed_by = %s
                        WHERE id = %s
                        """,
                        (new_body, new_status, reviewer, did),
                    )
                else:
                    cur.execute(
                        """
                        UPDATE drafts
                        SET status = 'approved',
                            reviewed_at = NOW(),
                            reviewed_by = %s
                        WHERE id = %s
                        """,
                        (reviewer, did),
                    )

    logger.info("DRAFT_APPROVED | draft_id=%s | reviewed_by=%s", did, reviewer)
    audit_event("draft_approved", draft_id=did, reviewed_by=reviewer)
    return get_draft(did)


def send_approved_draft(draft_id: str) -> str:
    did = require_non_empty(draft_id, "draft_id")
    draft = get_draft(did)

    if draft.status not in ("approved", "edited_and_approved"):
        raise ValueError(
            f"Draft {did} must be approved before send (status={draft.status!r})."
        )
    if draft.sent_at is not None:
        raise ValueError(f"Draft {did} was already sent.")

    body = draft.draft_body.strip()
    if not body:
        raise ValueError("Draft body is empty.")

    logger.info(
        "DRAFT_SEND_PLACEHOLDER | draft_id=%s | thread_id=%s | body_chars=%s",
        did,
        draft.thread_id,
        len(body),
    )

    state = load_thread_state(draft.thread_id)
    add_message_and_maybe_summarize(state, "assistant", body)
    persist_thread_state(state)

    warm_pg_runtime()
    with get_connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE drafts
                    SET sent_at = NOW()
                    WHERE id = %s AND sent_at IS NULL
                    RETURNING id
                    """,
                    (did,),
                )
                updated = cur.fetchone()
                if updated is None:
                    raise ValueError(f"Draft {did} was already sent.")

    logger.info("DRAFT_SENT | draft_id=%s | thread_id=%s", did, draft.thread_id)
    audit_event("draft_sent", draft_id=did, thread_id=draft.thread_id)
    return body
