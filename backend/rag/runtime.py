"""One-time RAG runtime warm-up (Qdrant, Cohere reranker, Gemini LLM)."""

import logging

from rag.generation import warm_generation_runtime
from rag.qdrant_store import warm_qdrant_runtime
from rag.reranking import warm_rerank_runtime

logger = logging.getLogger("fr8labs.rag")

_runtime_warmed = False


def warm_rag_runtime() -> None:
    """Warm external clients once per process. Safe to call multiple times."""
    global _runtime_warmed
    if _runtime_warmed:
        return

    warm_qdrant_runtime()
    warm_rerank_runtime()
    warm_generation_runtime()
    _runtime_warmed = True
    logger.info("RAG_READY")
