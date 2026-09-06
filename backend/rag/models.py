from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import UUID

from langchain_core.documents import Document


@dataclass(frozen=True)
class UploadedFile:
    document_id: UUID
    stored_path: Path
    content_hash: str
    uploaded_at: datetime
    original_filename: str


@dataclass(frozen=True)
class Citation:
    document_id: str
    original_filename: str
    chunk_index: int


@dataclass(frozen=True)
class DraftReplyResult:
    draft_text: str
    citations: list[Citation]
    rerank_succeeded: bool


def _chunk_meta(metadata: dict) -> dict:
    if not metadata:
        return {}
    nested = metadata.get("metadata")
    if isinstance(nested, dict):
        return nested
    return metadata


def citation_from_document(doc: Document) -> Citation:
    meta = _chunk_meta(doc.metadata)
    return Citation(
        document_id=str(meta.get("document_id", "unknown")),
        original_filename=str(meta.get("original_filename", "unknown")),
        chunk_index=int(meta.get("chunk_index", -1)),
    )
