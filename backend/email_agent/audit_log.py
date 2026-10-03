"""Append-only NDJSON audit log for email-agent events."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rag.config import settings

logger = logging.getLogger("fr8labs.email_agent.audit")


def _audit_path() -> Path:
    return Path(settings.EMAIL_AGENT_AUDIT_LOG)


def audit_event(event: str, **fields: Any) -> None:
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **fields,
    }
    path = _audit_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, default=str)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except OSError as exc:
        logger.warning("AUDIT_LOG_WRITE_FAILED | event=%s | error=%s", event, exc)
