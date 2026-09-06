import logging
import time
from collections.abc import Callable
from typing import TypeVar

from rag.config import settings

logger = logging.getLogger("fr8labs.retry")
T = TypeVar("T")


def is_rate_limit_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "429" in message or "rate limit" in message or "resource exhausted" in message


def call_with_rate_limit_retry(
    fn: Callable[[], T],
    *,
    label: str = "API call",
) -> T:
    max_retries = settings.EMBEDDING_MAX_RETRIES
    delay_sec = settings.EMBEDDING_BATCH_DELAY_SEC

    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception as exc:
            if not is_rate_limit_error(exc) or attempt >= max_retries:
                raise
            wait = delay_sec * (2 ** attempt)
            logger.warning("RATE_LIMIT_RETRY | label=%s | attempt=%s | wait_sec=%.1f", label, attempt + 1, wait)
            time.sleep(wait)

    raise RuntimeError(f"Rate limit retries exhausted for {label}")
