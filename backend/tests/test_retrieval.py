from unittest.mock import MagicMock, patch

from langchain_core.documents import Document
from qdrant_client.http import models

from rag.retrieval import hybrid_search, sanitize_email_content


def test_sanitize_email_content_strips_html():
    subject = "<b>Urgent</b> shipment"
    body = "<p>Please confirm <script>alert('x')</script> rates.</p>"
    result = sanitize_email_content(subject, body)
    assert "<" not in result
    assert "Urgent" in result
    assert "Please confirm" in result
    assert "alert" not in result


def test_sanitize_email_content_truncates(monkeypatch):
    monkeypatch.setattr("rag.retrieval.settings.EMAIL_MAX_CHARS", 50)
    result = sanitize_email_content("Long subject here", "x" * 100)
    assert len(result) == 50


@patch("rag.retrieval.get_vector_store")
def test_hybrid_search_applies_active_filter(mock_get_vector_store):
    mock_store = MagicMock()
    mock_get_vector_store.return_value = mock_store
    mock_store.similarity_search.return_value = [
        Document(page_content="chunk", metadata={"document_id": "abc", "active": True})
    ]

    results = hybrid_search("shipping rates", top_k=10)

    mock_get_vector_store.assert_called_once()
    mock_store.similarity_search.assert_called_once()
    call_kwargs = mock_store.similarity_search.call_args
    assert call_kwargs[0][0] == "shipping rates"
    assert call_kwargs[1]["k"] == 10
    filter_arg = call_kwargs[1]["filter"]
    assert isinstance(filter_arg, models.Filter)
    assert filter_arg.must[0].key == "metadata.active"
    assert filter_arg.must[0].match.value is True
    assert len(results) == 1
