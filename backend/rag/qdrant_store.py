import logging
from functools import lru_cache
from uuid import UUID

from langchain_qdrant import QdrantVectorStore, RetrievalMode
from qdrant_client import QdrantClient
from qdrant_client.http import models

from rag.config import settings
from rag.embeddings import get_dense_embeddings, get_sparse_embeddings

logger = logging.getLogger("fr8labs.qdrant")

PAYLOAD_INDEX_SPECS: dict[str, models.PayloadSchemaType] = {
    "metadata.document_id": models.PayloadSchemaType.KEYWORD,
    "metadata.active": models.PayloadSchemaType.BOOL,
}


def _chunk_meta(payload: dict) -> dict:
    if not payload:
        return {}
    nested = payload.get("metadata")
    if isinstance(nested, dict):
        return nested
    return payload


_payload_indexes_ready = False


@lru_cache(maxsize=1)
def get_client() -> QdrantClient:
    kwargs: dict = {"url": settings.QDRANT_URL}
    if settings.QDRANT_API_KEY:
        kwargs["api_key"] = settings.QDRANT_API_KEY
    return QdrantClient(**kwargs)


def ensure_collection(client: QdrantClient) -> None:
    name = settings.QDRANT_COLLECTION
    if not client.collection_exists(name):
        client.create_collection(
            collection_name=name,
            vectors_config={
                settings.QDRANT_DENSE_VECTOR_NAME: models.VectorParams(
                    size=settings.DENSE_EMBEDDING_DIM,
                    distance=models.Distance.COSINE,
                ),
            },
            sparse_vectors_config={
                settings.QDRANT_SPARSE_VECTOR_NAME: models.SparseVectorParams(
                    modifier=models.Modifier.IDF
                ),
            },
        )

    ensure_payload_indexes(client)


def ensure_payload_indexes(client: QdrantClient) -> None:
    global _payload_indexes_ready
    if _payload_indexes_ready:
        return

    name = settings.QDRANT_COLLECTION
    try:
        info = client.get_collection(name)
    except Exception:
        return

    existing = info.payload_schema or {}

    for field_name, field_schema in PAYLOAD_INDEX_SPECS.items():
        if field_name in existing:
            continue
        client.create_payload_index(
            collection_name=name,
            field_name=field_name,
            field_schema=field_schema,
        )

    _payload_indexes_ready = True


@lru_cache(maxsize=1)
def get_vector_store() -> QdrantVectorStore:
    """Reused across searches. Collection is validated once in warm_qdrant_runtime()."""
    client = get_client()
    return QdrantVectorStore(
        client=client,
        collection_name=settings.QDRANT_COLLECTION,
        embedding=get_dense_embeddings(),
        sparse_embedding=get_sparse_embeddings(),
        retrieval_mode=RetrievalMode.HYBRID,
        vector_name=settings.QDRANT_DENSE_VECTOR_NAME,
        sparse_vector_name=settings.QDRANT_SPARSE_VECTOR_NAME,
        validate_collection_config=False,
    )


def build_vector_store(_client: QdrantClient | None = None) -> QdrantVectorStore:
    """Return the shared vector store (client arg kept for ingest callers)."""
    return get_vector_store()


def warm_qdrant_runtime() -> None:
    """Connect to Qdrant once at startup."""
    client = get_client()
    ensure_payload_indexes(client)
    get_vector_store()
    logger.info("QDRANT_WARMED | collection=%s", settings.QDRANT_COLLECTION)


def list_documents(client: QdrantClient) -> list[dict]:
    name = settings.QDRANT_COLLECTION
    if not client.collection_exists(name):
        return []

    documents: dict[str, dict] = {}
    chunk_counts: dict[str, int] = {}
    offset = None

    while True:
        points, offset = client.scroll(
            collection_name=name,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        if not points:
            break

        for point in points:
            payload = point.payload or {}
            meta = _chunk_meta(payload)
            doc_id = meta.get("document_id")
            if not doc_id:
                continue

            chunk_counts[doc_id] = chunk_counts.get(doc_id, 0) + 1
            uploaded_at = meta.get("uploaded_at", "")

            if doc_id not in documents or uploaded_at >= documents[doc_id].get("uploaded_at", ""):
                documents[doc_id] = {
                    "document_id": doc_id,
                    "original_filename": meta.get("original_filename"),
                    "content_hash": meta.get("content_hash"),
                    "uploaded_at": uploaded_at,
                    "active": meta.get("active"),
                }

        if offset is None:
            break

    for doc_id, doc in documents.items():
        doc["chunk_count"] = chunk_counts.get(doc_id, 0)

    return sorted(documents.values(), key=lambda d: d.get("uploaded_at", ""), reverse=True)


def mark_superseded(client: QdrantClient, document_id: str | UUID) -> None:
    ensure_payload_indexes(client)
    name = settings.QDRANT_COLLECTION
    doc_id = str(document_id)
    filter_ = models.Filter(
        must=[
            models.FieldCondition(
                key="metadata.document_id",
                match=models.MatchValue(value=doc_id),
            )
        ]
    )

    client.set_payload(
        collection_name=name,
        payload={"metadata": {"active": False}},
        points=models.FilterSelector(filter=filter_),
    )
    client.delete(
        collection_name=name,
        points_selector=models.FilterSelector(filter=filter_),
    )
