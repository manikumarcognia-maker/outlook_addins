from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ThreadMessage:
    role: str  # "customer" | "assistant"
    body: str
    id: str | None = None
    is_summarized: bool = False
    source_message_id: str | None = None


@dataclass
class ThreadState:
    thread_id: str
    customer_id: str
    facts: dict[str, dict[str, object]] = field(default_factory=dict)
    summary: str = ""
    recent_messages: list[ThreadMessage] = field(default_factory=list)
    folded_messages: list[ThreadMessage] = field(default_factory=list)
    known_source_message_ids: set[str] = field(default_factory=set)
