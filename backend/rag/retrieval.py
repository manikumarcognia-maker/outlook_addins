import logging
import re

from langchain_core.documents import Document
from qdrant_client.http import models

from app.observability import trace_step
from rag.config import settings
from rag.qdrant_store import get_vector_store

logger = logging.getLogger("fr8labs.retrieval")

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_SCRIPT_STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_WHITESPACE_RE = re.compile(r"\s+")


def _strip_html(text: str) -> str:
    text = _SCRIPT_STYLE_RE.sub(" ", text)
    text = _HTML_TAG_RE.sub(" ", text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def sanitize_email_content(subject: str, body: str) -> str:
    clean_subject = _strip_html(subject or "").strip()
    clean_body = _strip_html(body or "").strip()

    parts: list[str] = []
    if clean_subject:
        parts.append(f"Subject: {clean_subject}")
    if clean_body:
        if parts:
            parts.append("")
        parts.append(clean_body)

    combined = "\n".join(parts).strip()
    if len(combined) > settings.EMAIL_MAX_CHARS:
        combined = combined[: settings.EMAIL_MAX_CHARS]
    return combined


def _active_filter() -> models.Filter:
    return models.Filter(
        must=[
            models.FieldCondition(
                key="metadata.active",
                match=models.MatchValue(value=True),
            )
        ]
    )


def hybrid_search(query_text: str, top_k: int | None = None) -> list[Document]:
    k = top_k if top_k is not None else settings.RETRIEVAL_TOP_K
    with trace_step(
        "qdrant_hybrid_search",
        logger,
        top_k=k,
        collection=settings.QDRANT_COLLECTION,
        query_chars=len(query_text),
    ):
        vector_store = get_vector_store()
        results = vector_store.similarity_search(
            query_text,
            k=k,
            filter=_active_filter(),
        )
        logger.info("QDRANT_SEARCH_DONE | returned=%s", len(results))
        return results
