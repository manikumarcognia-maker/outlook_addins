from unittest.mock import MagicMock, patch

from langchain_core.documents import Document

from rag.reranking import rerank_candidates


def _docs(*texts: str) -> list[Document]:
    return [Document(page_content=t, metadata={"chunk_index": i}) for i, t in enumerate(texts)]


@patch("rag.reranking.get_reranker")
def test_rerank_candidates_happy_path(mock_get_reranker):
    candidates = _docs("a", "b", "c")
    reranked = _docs("c", "a")
    mock_reranker = MagicMock()
    mock_reranker.compress_documents.return_value = reranked
    mock_get_reranker.return_value = mock_reranker

    result, succeeded = rerank_candidates("query", candidates, top_n=2)

    assert succeeded is True
    assert result == reranked
    mock_reranker.compress_documents.assert_called_once()


@patch("rag.reranking.get_reranker")
def test_rerank_candidates_fallback_on_failure(mock_get_reranker):
    candidates = _docs("first", "second", "third")
    mock_reranker = MagicMock()
    mock_reranker.compress_documents.side_effect = RuntimeError("rate limited")
    mock_get_reranker.return_value = mock_reranker

    result, succeeded = rerank_candidates("query", candidates, top_n=2)

    assert succeeded is False
    assert len(result) == 2
    assert result[0].page_content == "first"
    assert result[1].page_content == "second"
