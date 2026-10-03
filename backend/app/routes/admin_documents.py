import tempfile
from pathlib import Path

import psycopg
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from rag.config import settings
from rag.ingest import ingest_file
from rag.loaders import SUPPORTED_EXTENSIONS
from rag.models import citation_from_document
from rag.pg_store import list_documents, mark_superseded
from rag.retrieval import hybrid_search

router = APIRouter()

SNIPPET_LENGTH = 200


class UploadResponse(BaseModel):
    document_id: str
    chunk_count: int
    original_filename: str


class SearchPreviewItem(BaseModel):
    document_id: str
    original_filename: str
    chunk_index: int
    snippet: str


def _validate_upload(file: UploadFile, content: bytes) -> None:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    extension = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if extension not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{extension}'. Supported: {supported}",
        )

    if not content:
        raise HTTPException(status_code=400, detail="File is empty.")

    if len(content) > settings.MAX_UPLOAD_BYTES:
        max_mb = settings.MAX_UPLOAD_BYTES / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum size of {max_mb:.0f} MB.",
        )


def _http_error_for_exception(exc: Exception) -> HTTPException:
    message = str(exc)
    lowered = message.lower()
    if isinstance(exc, ValueError):
        return HTTPException(status_code=400, detail=message)
    if "429" in message or "rate limit" in lowered or "resource exhausted" in lowered:
        return HTTPException(status_code=502, detail=message)
    if isinstance(exc, psycopg.Error) or "connection" in lowered or "ssl" in lowered:
        return HTTPException(
            status_code=503,
            detail="Database temporarily unavailable. Wait a few seconds and retry.",
        )
    return HTTPException(status_code=500, detail=message)


def _find_document(document_id: str) -> dict | None:
    for doc in list_documents():
        if doc.get("document_id") == document_id:
            return doc
    return None


@router.get("/documents/supported-types")
def get_supported_types() -> list[str]:
    return sorted(SUPPORTED_EXTENSIONS)


@router.post("/documents/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
):
    content = await file.read()
    _validate_upload(file, content)

    extension = Path(file.filename or "").suffix.lower()
    tmp_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        document_id = ingest_file(str(tmp_path))
        doc = _find_document(document_id)
        if not doc:
            raise HTTPException(
                status_code=500,
                detail=f"Ingest completed but document {document_id} was not found in index.",
            )

        return UploadResponse(
            document_id=document_id,
            chunk_count=doc.get("chunk_count", 0),
            original_filename=doc.get("original_filename") or file.filename or "",
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise _http_error_for_exception(exc) from exc
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink()


@router.get("/documents")
def get_documents() -> list[dict]:
    try:
        return list_documents()
    except Exception as exc:
        raise _http_error_for_exception(exc) from exc


@router.post("/documents/{document_id}/supersede")
def supersede_document(document_id: str) -> dict:
    try:
        mark_superseded(document_id)
    except Exception as exc:
        raise _http_error_for_exception(exc) from exc
    return {"document_id": document_id, "superseded": True}


@router.get("/search-preview", response_model=list[SearchPreviewItem])
def search_preview(q: str, top_k: int = 5) -> list[SearchPreviewItem]:
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required.")

    top_k = min(max(top_k, 1), 30)

    try:
        results = hybrid_search(q.strip(), top_k=top_k)
    except Exception as exc:
        raise _http_error_for_exception(exc) from exc

    items: list[SearchPreviewItem] = []
    for doc in results:
        citation = citation_from_document(doc)
        snippet = doc.page_content[:SNIPPET_LENGTH]
        if len(doc.page_content) > SNIPPET_LENGTH:
            snippet += "..."
        items.append(
            SearchPreviewItem(
                document_id=citation.document_id,
                original_filename=citation.original_filename,
                chunk_index=citation.chunk_index,
                snippet=snippet,
            )
        )
    return items
