"""Inbound conversation message payloads (Graph sync)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

MAX_CONVERSATION_MESSAGES = 20


@dataclass(frozen=True)
class InboundConversationMessage:
    source_message_id: str
    body: str
    received_at: datetime | None = None


@dataclass(frozen=True)
class ThreadSyncResult:
    synced_count: int
    skipped_count: int
    synced_source_message_ids: list[str]


def normalize_conversation_messages(
    *,
    trigger_source_message_id: str,
    trigger_body: str,
    conversation_messages: list[InboundConversationMessage] | None,
) -> list[InboundConversationMessage]:
    """Build ordered sync list; default to single trigger message when array omitted."""
    if conversation_messages is None or len(conversation_messages) == 0:
        return [
            InboundConversationMessage(
                source_message_id=trigger_source_message_id.strip(),
                body=trigger_body.strip(),
            )
        ]

    if len(conversation_messages) > MAX_CONVERSATION_MESSAGES:
        raise ValueError(
            f"conversation_messages exceeds maximum of {MAX_CONVERSATION_MESSAGES}."
        )

    seen_ids: set[str] = set()
    normalized: list[InboundConversationMessage] = []
    for item in conversation_messages:
        sid = item.source_message_id.strip()
        body = item.body.strip()
        if not sid:
            raise ValueError("conversation_messages entry missing source_message_id.")
        if not body:
            raise ValueError("conversation_messages entry missing body.")
        if sid in seen_ids:
            raise ValueError("conversation_messages contains duplicate source_message_id.")
        seen_ids.add(sid)
        normalized.append(
            InboundConversationMessage(
                source_message_id=sid,
                body=body,
                received_at=item.received_at,
            )
        )

    trigger = trigger_source_message_id.strip()
    if trigger not in seen_ids:
        raise ValueError(
            "trigger source_message_id must appear in conversation_messages."
        )

    def sort_key(msg: InboundConversationMessage) -> tuple[int, str]:
        if msg.received_at is not None:
            return (0, msg.received_at.isoformat())
        return (1, msg.source_message_id)

    return sorted(normalized, key=sort_key)
