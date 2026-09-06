from langchain_core.documents import Document

from rag.chunking import split_into_chunks
from rag.document_store import save_uploaded_file
from rag.loaders import load_document
from rag.models import UploadedFile
from rag.qdrant_store import build_vector_store, ensure_collection, get_client


def attach_chunk_metadata(
    chunks: list[Document],
    uploaded: UploadedFile,
) -> list[Document]:
    uploaded_at = uploaded.uploaded_at.isoformat()
    doc_id = str(uploaded.document_id)

    for index, chunk in enumerate(chunks):
        chunk.metadata.update(
            {
                "document_id": doc_id,
                "original_filename": uploaded.original_filename,
                "content_hash": uploaded.content_hash,
                "uploaded_at": uploaded_at,
                "active": True,
                "chunk_index": index,
            }
        )
    return chunks


def ingest_file(source_path: str) -> str:
    print(f"Ingesting: {source_path}")

    uploaded = save_uploaded_file(source_path)
    print(f"Saved raw file as document_id={uploaded.document_id}")

    documents = load_document(uploaded.stored_path)
    chunks = split_into_chunks(documents)
    print(f"Split into {len(chunks)} chunks")

    if not chunks:
        raise ValueError("No text content found in document")

    chunks = attach_chunk_metadata(chunks, uploaded)

    client = get_client()
    ensure_collection(client)
    vector_store = build_vector_store(client)

    print("Embedding and upserting to Qdrant (dense + sparse hybrid)...")
    vector_store.add_documents(chunks)
    print(f"Done. document_id={uploaded.document_id}")

    return str(uploaded.document_id)
