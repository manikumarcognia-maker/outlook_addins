"""Load and persist email-thread session state (Postgres)."""

from __future__ import annotations

import json
import logging

from email_agent.models import ThreadMessage, ThreadState
from email_agent.validation import require_non_empty
from rag.pg_store import get_connection, warm_pg_runtime

logger = logging.getLogger("fr8labs.email_agent.store")


def load_thread_state(thread_id: str) -> ThreadState:
    """Load thread state from the DB, creating a new ``threads`` row if missing."""
    tid = require_non_empty(thread_id, "thread_id")
    warm_pg_runtime()

    with get_connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT customer_id FROM threads WHERE thread_id = %s",
                    (tid,),
                )
                row = cur.fetchone()
                if row is None:
                    cur.execute(
                        """
                        INSERT INTO threads (thread_id, customer_id)
                        VALUES (%s, '')
                        """,
                        (tid,),
                    )
                    cid = ""
                    logger.debug("THREAD_CREATED | thread_id=%s", tid)
                else:
                    cid = row["customer_id"]
                    logger.debug("THREAD_LOADED | thread_id=%s", tid)

                cur.execute(
                    """
                    SELECT subject_id, facts
                    FROM shipment_facts
                    WHERE thread_id = %s
                    """,
                    (tid,),
                )
                facts: dict[str, dict[str, object]] = {}
                for fact_row in cur.fetchall():
                    subject_id = fact_row["subject_id"]
                    raw_facts = fact_row["facts"]
                    if isinstance(raw_facts, dict):
                        facts[subject_id] = dict(raw_facts)
                    else:
                        facts[subject_id] = {}

                cur.execute(
                    "SELECT summary FROM thread_summary WHERE thread_id = %s",
                    (tid,),
                )
                summary_row = cur.fetchone()
                summary = summary_row["summary"] if summary_row else ""

                cur.execute(
                    """
                    SELECT source_message_id
                    FROM thread_messages
                    WHERE thread_id = %s AND source_message_id IS NOT NULL
                    """,
                    (tid,),
                )
                known_source_message_ids = {
                    str(row["source_message_id"]) for row in cur.fetchall()
                }

                cur.execute(
                    """
                    SELECT id, role, body, source_message_id
                    FROM thread_messages
                    WHERE thread_id = %s AND is_summarized = false
                    ORDER BY created_at ASC
                    """,
                    (tid,),
                )
                recent_messages = [
                    ThreadMessage(
                        role=m["role"],
                        body=m["body"],
                        id=str(m["id"]),
                        is_summarized=False,
                        source_message_id=m.get("source_message_id"),
                    )
                    for m in cur.fetchall()
                ]

    return ThreadState(
        thread_id=tid,
        customer_id=cid,
        facts=facts,
        summary=summary,
        recent_messages=recent_messages,
        known_source_message_ids=known_source_message_ids,
    )


def _insert_message(
    cur,
    thread_id: str,
    message: ThreadMessage,
) -> None:
    cur.execute(
        """
        INSERT INTO thread_messages (
          thread_id, role, body, is_summarized, source_message_id
        )
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            thread_id,
            message.role,
            message.body,
            message.is_summarized,
            message.source_message_id,
        ),
    )
    row = cur.fetchone()
    if row is not None:
        message.id = str(row["id"])


def _persist_folded_message(cur, thread_id: str, message: ThreadMessage) -> None:
    if message.id is not None:
        cur.execute(
            """
            UPDATE thread_messages
            SET is_summarized = true
            WHERE id = %s AND thread_id = %s
            """,
            (message.id, thread_id),
        )
        return
    _insert_message(cur, thread_id, message)


def persist_thread_state(state: ThreadState) -> None:
    """Write facts, summary, and messages back to the DB in one transaction."""
    tid = require_non_empty(state.thread_id, "thread_id")
    warm_pg_runtime()

    with get_connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                for subject_id, facts_dict in state.facts.items():
                    cur.execute(
                        """
                        INSERT INTO shipment_facts (
                          thread_id, subject_id, facts, updated_at
                        ) VALUES (%s, %s, %s::jsonb, NOW())
                        ON CONFLICT (thread_id, subject_id) DO UPDATE
                          SET facts = EXCLUDED.facts,
                              updated_at = NOW()
                        """,
                        (tid, subject_id, json.dumps(facts_dict)),
                    )

                cur.execute(
                    """
                    INSERT INTO thread_summary (thread_id, summary, updated_at)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (thread_id) DO UPDATE
                      SET summary = EXCLUDED.summary,
                          updated_at = NOW()
                    """,
                    (tid, state.summary),
                )

                for message in state.folded_messages:
                    _persist_folded_message(cur, tid, message)

                for message in state.recent_messages:
                    if message.id is None:
                        _insert_message(cur, tid, message)

    state.folded_messages.clear()
    logger.info("THREAD_PERSISTED | thread_id=%s", tid)
