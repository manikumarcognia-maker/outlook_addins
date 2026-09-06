import time
from functools import lru_cache
from typing import Sequence

from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from rag.bm25_sparse import get_sparse_embeddings
from rag.config import settings
from rag.retry import call_with_rate_limit_retry, is_rate_limit_error


class RateLimitedEmbeddings(Embeddings):
    """Wraps dense embeddings with batching, delay, and 429 backoff."""

    def __init__(self, inner: GoogleGenerativeAIEmbeddings):
        self._inner = inner

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return embed_documents_with_retry(self._inner, texts)

    def embed_query(self, text: str) -> list[float]:
        return call_with_rate_limit_retry(
            lambda: self._inner.embed_query(text),
            label="embedding query",
        )


@lru_cache(maxsize=1)
def get_dense_embeddings() -> Embeddings:
    inner = GoogleGenerativeAIEmbeddings(
        model=settings.GEMINI_EMBEDDING_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
    )
    return RateLimitedEmbeddings(inner)


# Sparse embeddings: see rag/bm25_sparse.py (re-exported for callers)
def embed_documents_with_retry(
    embeddings: Embeddings,
    texts: Sequence[str],
) -> list[list[float]]:
    if not texts:
        return []

    batch_size = settings.EMBEDDING_BATCH_SIZE
    max_retries = settings.EMBEDDING_MAX_RETRIES
    delay_sec = settings.EMBEDDING_BATCH_DELAY_SEC
    results: list[list[float]] = []

    for start in range(0, len(texts), batch_size):
        batch = list(texts[start : start + batch_size])
        for attempt in range(max_retries + 1):
            try:
                vectors = embeddings.embed_documents(batch)
                results.extend(vectors)
                break
            except Exception as exc:
                if not is_rate_limit_error(exc) or attempt >= max_retries:
                    raise
                wait = delay_sec * (2 ** attempt)
                print(
                    f"Rate limited on embedding batch {start // batch_size + 1}, "
                    f"retrying in {wait:.1f}s..."
                )
                time.sleep(wait)

        if start + batch_size < len(texts):
            time.sleep(delay_sec)

    return results
