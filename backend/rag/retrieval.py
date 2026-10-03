import logging
import re

from langchain_core.documents import Document

from app.observability import trace_step
from rag.config import settings
from rag.embeddings import get_dense_embeddings
from rag.pg_store import dense_search

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


def hybrid_search(
    query_text: str,
    top_k: int | None = None,
    company_id: str | None = None,
) -> list[Document]:
    k = top_k if top_k is not None else settings.RETRIEVAL_TOP_K
    cid = company_id or settings.DEFAULT_COMPANY_ID
    query_vector = get_dense_embeddings().embed_query(query_text)
    with trace_step(
        "pgvector_dense_search",
        logger,
        top_k=k,
        company_id=cid,
        query_chars=len(query_text),
    ):
        results = dense_search(query_vector, k, company_id=company_id)
        logger.info("PGVECTOR_SEARCH_DONE | returned=%s", len(results))
        return results
