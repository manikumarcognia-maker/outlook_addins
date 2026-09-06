import logging
from functools import lru_cache

from langchain_core.documents import Document
from langchain_cohere import CohereRerank

from rag.config import settings

logger = logging.getLogger("fr8labs.reranking")

MAX_RERANK_DOCS = 30


@lru_cache(maxsize=1)
def get_reranker() -> CohereRerank:
    return CohereRerank(
        model=settings.COHERE_RERANK_MODEL,
        cohere_api_key=settings.COHERE_API_KEY,
        top_n=settings.RERANK_TOP_N,
    )


def warm_rerank_runtime() -> None:
    get_reranker()
    logger.info("COHERE_RERANK_WARMED | model=%s", settings.COHERE_RERANK_MODEL)


def rerank_candidates(
    query_text: str,
    candidates: list[Document],
    top_n: int | None = None,
) -> tuple[list[Document], bool]:
    if not candidates:
        return [], False

    final_n = top_n if top_n is not None else settings.RERANK_TOP_N
    final_n = min(final_n, len(candidates), MAX_RERANK_DOCS)
    pool = candidates[:MAX_RERANK_DOCS]

    try:
        reranker = get_reranker()
        reranked = reranker.compress_documents(documents=pool, query=query_text)[:final_n]
        logger.info("COHERE_RERANK_OK | returned=%s", len(reranked))
        return reranked, True
    except Exception as exc:
        logger.warning("COHERE_RERANK_FALLBACK | error=%s", exc)
        return pool[:final_n], False
