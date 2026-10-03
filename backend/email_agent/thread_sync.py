"""Sync conversation messages into thread state (facts + message buffer)."""

from __future__ import annotations

from email_agent.conversation import InboundConversationMessage, ThreadSyncResult
from email_agent.facts import extract_facts, merge_facts
from email_agent.messages import add_message_and_maybe_summarize
from email_agent.models import ThreadState
from email_agent.pipeline_audit import audit_pipeline_extraction


def sync_customer_messages(
    state: ThreadState,
    messages: list[InboundConversationMessage],
    *,
    thread_id: str,
) -> ThreadSyncResult:
    """Extract and append each message not already stored by source_message_id."""
    synced_ids: list[str] = []
    skipped = 0

    for message in messages:
        sid = message.source_message_id
        if sid in state.known_source_message_ids:
            skipped += 1
            continue

        extraction = extract_facts(message.body)
        merge_facts(state, extraction)
        audit_pipeline_extraction(
            thread_id=thread_id,
            source_message_id=sid,
            email_preview=message.body,
            extraction=extraction,
        )
        add_message_and_maybe_summarize(
            state,
            "customer",
            message.body,
            source_message_id=sid,
        )
        state.known_source_message_ids.add(sid)
        synced_ids.append(sid)

    return ThreadSyncResult(
        synced_count=len(synced_ids),
        skipped_count=skipped,
        synced_source_message_ids=synced_ids,
    )
