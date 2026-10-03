"""Inbound email orchestration: thread state → draft for human review (no auto-send).

Entry: ``POST /api/email-agent/inbound`` only (Outlook add-in **Generate**).
Do not call from Graph mail webhooks or background jobs without an explicit product decision.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.observability import trace_step
from email_agent.audit_log import audit_event
from email_agent.coordinator import RefinementResult, refine_search_query
from email_agent.conversation import (
    InboundConversationMessage,
    normalize_conversation_messages,
)
from email_agent.pipeline_audit import (
    audit_pipeline_refine,
    audit_pipeline_retrieval,
    audit_pipeline_synthesis,
    audit_pipeline_thread_persisted,
    audit_pipeline_thread_sync,
)
from email_agent.drafts import get_draft_id_for_message, save_draft_for_review
from email_agent.store import load_thread_state, persist_thread_state
from email_agent.synthesis import synthesize_reply
from email_agent.thread_sync import sync_customer_messages
from email_agent.retrieval import RetrievalResult, retrieve_with_retry
from email_agent.validation import require_non_empty

logger = logging.getLogger("fr8labs.email_agent.pipeline")


@dataclass(frozen=True)
class InboundResult:
    draft_id: str
    duplicate: bool = False


def handle_inbound_email(
    thread_id: str,
    email_body: str,
    *,
    source_message_id: str,
    conversation_messages: list[InboundConversationMessage] | None = None,
) -> InboundResult:
    """Run the full thread agent pipeline; return draft_id (pending_review)."""
    tid = require_non_empty(thread_id, "thread_id")
    body = require_non_empty(email_body, "email_body")
    message_id = require_non_empty(source_message_id, "source_message_id")

    existing = get_draft_id_for_message(tid, message_id)
    if existing is not None:
        logger.info(
            "INBOUND_DUPLICATE | thread_id=%s | source_message_id=%s | draft_id=%s",
            tid,
            message_id,
            existing,
        )
        audit_event(
            "inbound_duplicate",
            thread_id=tid,
            source_message_id=message_id,
            draft_id=existing,
        )
        return InboundResult(draft_id=existing, duplicate=True)

    messages_to_sync = normalize_conversation_messages(
        trigger_source_message_id=message_id,
        trigger_body=body,
        conversation_messages=conversation_messages,
    )

    with trace_step("inbound_load_thread", logger, thread_id=tid):
        state = load_thread_state(tid)

    with trace_step("inbound_sync_thread", logger, thread_id=tid):
        sync_result = sync_customer_messages(
            state,
            messages_to_sync,
            thread_id=tid,
        )
        audit_pipeline_thread_sync(
            thread_id=tid,
            trigger_source_message_id=message_id,
            sync_result=sync_result,
        )

    with trace_step("inbound_persist_thread", logger, thread_id=tid):
        persist_thread_state(state)
        audit_pipeline_thread_persisted(thread_id=tid, state=state)

    with trace_step("inbound_refine_query", logger, thread_id=tid):
        refined: RefinementResult = refine_search_query(state, body)
        audit_pipeline_refine(thread_id=tid, refined=refined)

    with trace_step(
        "inbound_retrieve",
        logger,
        thread_id=tid,
        query_chars=len(refined.query),
    ):
        retrieval_result: RetrievalResult = retrieve_with_retry(
            refined.query,
            refined.filters,
        )
        audit_pipeline_retrieval(
            thread_id=tid,
            search_query=refined.query,
            retrieval_result=retrieval_result,
        )

    with trace_step(
        "inbound_synthesize",
        logger,
        thread_id=tid,
        retrieval_outcome=retrieval_result["status"],
    ):
        synthesis = synthesize_reply(state, retrieval_result, body)
        audit_pipeline_synthesis(thread_id=tid, synthesis=synthesis)

    with trace_step("inbound_save_draft", logger, thread_id=tid):
        draft_id = save_draft_for_review(
            tid,
            synthesis,
            source_message_id=message_id,
        )

    logger.info(
        "INBOUND_COMPLETE | thread_id=%s | draft_id=%s | retrieval_status=%s",
        tid,
        draft_id,
        synthesis.retrieval_status,
    )
    audit_event(
        "inbound_complete",
        thread_id=tid,
        draft_id=draft_id,
        retrieval_status=synthesis.retrieval_status,
        source_message_id=message_id,
    )
    return InboundResult(draft_id=draft_id, duplicate=False)
