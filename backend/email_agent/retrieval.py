"""KB retrieval for email agent: delegate to rag.hybrid_search + retry policy."""

from __future__ import annotations

import logging
import time
from typing import Any, Literal, TypedDict

import psycopg
from langchain_core.documents import Document

from email_agent.audit_log import audit_event
from email_agent.constants import RETRIEVAL_BACKOFF_BASE_SEC, RETRIEVAL_MAX_ATTEMPTS
from rag.retrieval import hybrid_search

logger = logging.getLogger("fr8labs.email_agent.retrieval")

EMPTY_RETRIEVAL_MESSAGE = (
    "No matching knowledge-base chunks were found for this query."
)

TRANSIENT_ALTERNATIVE_APPROACHES = [
    "Retry retrieval later when infrastructure may have recovered.",
    "Answer from thread facts and summary only, and note the knowledge-base gap.",
    "Have the rep search internal documents manually if policy requires KB confirmation.",
]


class TransientError(Exception):
    """Infrastructure failure that may succeed on retry (not an empty search result)."""


class RetrievedChunk(TypedDict):
    content: str
    document_id: str
    original_filename: str
    chunk_index: int


class RetrievalSuccess(TypedDict):
    status: Literal["success"]
    results: list[RetrievedChunk]


class RetrievalEmpty(TypedDict):
    status: Literal["success"]
    results: list[RetrievedChunk]
    message: str
    shouldRetry: bool


class RetrievalTransientError(TypedDict):
    status: Literal["error"]
    failureType: Literal["transient"]
    attemptedAction: dict[str, Any]
    partialResults: list[RetrievedChunk]
    alternativeApproaches: list[str]
    shouldRetry: bool


RetrievalResult = RetrievalSuccess | RetrievalEmpty | RetrievalTransientError


def _is_transient_failure(exc: BaseException) -> bool:
    if isinstance(exc, TransientError):
        return True
    if isinstance(exc, (psycopg.OperationalError, psycopg.InterfaceError)):
        return True
    if isinstance(exc, (TimeoutError, ConnectionError, OSError)):
        return True
    message = str(exc).lower()
    if "429" in message or "rate limit" in message or "resource exhausted" in message:
        return True
    if "503" in message or "service unavailable" in message:
        return True
    return False


def _reraise_search_failure(exc: BaseException) -> None:
    if not _is_transient_failure(exc):
        raise exc
    if isinstance(exc, TransientError):
        raise exc
    raise TransientError(str(exc)) from exc


def _document_to_chunk(doc: Document) -> RetrievedChunk:
    meta = doc.metadata or {}
    chunk_index = meta.get("chunk_index", 0)
    try:
        chunk_index = int(chunk_index)
    except (TypeError, ValueError):
        chunk_index = 0
    return RetrievedChunk(
        content=doc.page_content,
        document_id=str(meta.get("document_id", "")),
        original_filename=str(meta.get("original_filename", "")),
        chunk_index=chunk_index,
    )


def semantic_search(query: str, filters: dict[str, Any] | None = None) -> list[RetrievedChunk]:
    """Delegate to rag.hybrid_search and map documents to synthesis-friendly chunks."""
    filters = filters or {}
    top_k = filters.get("top_k")
    company_id = filters.get("company_id")
    try:
        documents = hybrid_search(
            query,
            top_k=top_k if top_k is not None else None,
            company_id=company_id if company_id is not None else None,
        )
    except Exception as exc:
        _reraise_search_failure(exc)
    return [_document_to_chunk(doc) for doc in documents]


def retrieve_with_retry(
    query: str,
    filters: dict[str, Any] | None = None,
    *,
    attempts: int = RETRIEVAL_MAX_ATTEMPTS,
) -> RetrievalResult:
    """Run KB search with transient retries; empty results never retry."""
    if attempts < 1:
        raise ValueError("attempts must be at least 1.")
    query = query.strip()
    if not query:
        raise ValueError("query is required and cannot be empty.")

    filters = dict(filters or {})

    for attempt in range(attempts):
        try:
            results = semantic_search(query, filters)
        except TransientError as exc:
            logger.warning(
                "RETRIEVAL_TRANSIENT | attempt=%s/%s | error=%s",
                attempt + 1,
                attempts,
                exc,
            )
            audit_event(
                "retrieval_transient",
                attempt=attempt + 1,
                max_attempts=attempts,
                error=str(exc),
            )
            if attempt < attempts - 1:
                time.sleep(RETRIEVAL_BACKOFF_BASE_SEC ** attempt)
                continue
            break
        except Exception:
            raise

        if results:
            return RetrievalSuccess(status="success", results=results)

        return RetrievalEmpty(
            status="success",
            results=[],
            message=EMPTY_RETRIEVAL_MESSAGE,
            shouldRetry=False,
        )

    error_result = RetrievalTransientError(
        status="error",
        failureType="transient",
        attemptedAction={"query": query, "filters": filters},
        partialResults=[],
        alternativeApproaches=list(TRANSIENT_ALTERNATIVE_APPROACHES),
        shouldRetry=True,
    )
    audit_event(
        "retrieval_exhausted",
        query_chars=len(query),
        filter_keys=list(filters.keys()),
    )
    return error_result
