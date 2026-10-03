"""Neon PostgreSQL + pgvector storage for company RAG chunks."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from functools import lru_cache
from typing import Iterator
from uuid import UUID

from langchain_core.documents import Document
import psycopg
from pgvector.psycopg import register_vector
from psycopg import Connection
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from rag.config import settings
from rag.models import UploadedFile
from rag.pg_conn import (
    POOL_WAIT_TIMEOUT_SEC,
    build_database_conninfo,
    clear_dns_cache,
    connection_kwargs,
)

logger = logging.getLogger("fr8labs.pgvector")

_runtime_warmed = False


def _tables_sql() -> str:
    dim = settings.DENSE_EMBEDDING_DIM
    return f"""
CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY,
  company_id TEXT NOT NULL,
  original_filename TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  uploaded_at TIMESTAMPTZ NOT NULL,
  active BOOLEAN NOT NULL DEFAULT true,
  stored_path TEXT
);

CREATE TABLE IF NOT EXISTS document_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  chunk_index INT NOT NULL,
  content TEXT NOT NULL,
  embedding vector({dim}) NOT NULL,
  UNIQUE (document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_documents_company_active
  ON documents (company_id, active);

CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id
  ON document_chunks (document_id);
"""


def ensure_schema(conn: Connection) -> None:
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    conn.commit()
    register_vector(conn)
    with conn.cursor() as cur:
        cur.execute(_tables_sql())
    conn.commit()


_pool: ConnectionPool | None = None


@lru_cache(maxsize=1)
def _database_conninfo() -> str:
    return build_database_conninfo(settings.DATABASE_URL)


def _configure_connection(conn: Connection) -> None:
    register_vector(conn)


@lru_cache(maxsize=1)
def get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=_database_conninfo(),
            min_size=0,
            max_size=5,
            timeout=POOL_WAIT_TIMEOUT_SEC,
            max_idle=60,
            max_lifetime=600,
            check=ConnectionPool.check_connection,
            configure=_configure_connection,
            kwargs={"row_factory": dict_row, **connection_kwargs()},
        )
        _pool.open(wait=False)
    return _pool


def _invalidate_connection_cache() -> None:
    global _pool
    _pool = None
    clear_dns_cache()
    get_pool.cache_clear()
    _database_conninfo.cache_clear()


def _connect_direct() -> Connection:
    try:
        return psycopg.connect(
            _database_conninfo(),
            row_factory=dict_row,
            **connection_kwargs(),
        )
    except psycopg.OperationalError:
        _invalidate_connection_cache()
        return psycopg.connect(
            build_database_conninfo(settings.DATABASE_URL),
            row_factory=dict_row,
            **connection_kwargs(),
        )


@contextmanager
def get_connection() -> Iterator[Connection]:
    pool = get_pool()
    with pool.connection() as conn:
        yield conn


def warm_pg_runtime() -> None:
    global _runtime_warmed
    if _runtime_warmed:
        return
    with _connect_direct() as conn:
        ensure_schema(conn)
    _runtime_warmed = True
    logger.info("PGVECTOR_WARMED | company_id=%s", settings.DEFAULT_COMPANY_ID)


def insert_document_with_chunks(
    uploaded: UploadedFile,
    chunks: list[Document],
    dense_vectors: list[list[float]],
    company_id: str | None = None,
) -> None:
    if len(chunks) != len(dense_vectors):
        raise ValueError("chunks and dense_vectors length mismatch")

    cid = company_id or settings.DEFAULT_COMPANY_ID
    warm_pg_runtime()

    with get_connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO documents (
                      id, company_id, original_filename, content_hash,
                      uploaded_at, active, stored_path
                    ) VALUES (%s, %s, %s, %s, %s, true, %s)
                    """,
                    (
                        uploaded.document_id,
                        cid,
                        uploaded.original_filename,
                        uploaded.content_hash,
                        uploaded.uploaded_at,
                        str(uploaded.stored_path),
                    ),
                )
                for chunk, vector in zip(chunks, dense_vectors, strict=True):
                    meta = chunk.metadata
                    chunk_index = int(meta.get("chunk_index", 0))
                    cur.execute(
                        """
                        INSERT INTO document_chunks (
                          document_id, chunk_index, content, embedding
                        ) VALUES (%s, %s, %s, %s)
                        """,
                        (
                            uploaded.document_id,
                            chunk_index,
                            chunk.page_content,
                            vector,
                        ),
                    )


def list_documents(company_id: str | None = None) -> list[dict]:
    cid = company_id or settings.DEFAULT_COMPANY_ID
    warm_pg_runtime()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                  d.id::text AS document_id,
                  d.original_filename,
                  d.content_hash,
                  d.uploaded_at,
                  d.active,
                  COUNT(c.id)::int AS chunk_count
                FROM documents d
                LEFT JOIN document_chunks c ON c.document_id = d.id
                WHERE d.company_id = %s
                GROUP BY d.id, d.original_filename, d.content_hash, d.uploaded_at, d.active
                ORDER BY d.uploaded_at DESC
                """,
                (cid,),
            )
            rows = cur.fetchall()

    result: list[dict] = []
    for row in rows:
        uploaded_at = row["uploaded_at"]
        result.append(
            {
                "document_id": row["document_id"],
                "original_filename": row["original_filename"],
                "content_hash": row["content_hash"],
                "uploaded_at": uploaded_at.isoformat() if uploaded_at else "",
                "active": row["active"],
                "chunk_count": row["chunk_count"] or 0,
            }
        )
    return result


def mark_superseded(document_id: str | UUID, company_id: str | None = None) -> None:
    cid = company_id or settings.DEFAULT_COMPANY_ID
    doc_id = UUID(str(document_id))
    warm_pg_runtime()

    with get_connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM document_chunks c
                    USING documents d
                    WHERE c.document_id = d.id
                      AND d.id = %s
                      AND d.company_id = %s
                    """,
                    (doc_id, cid),
                )
                cur.execute(
                    """
                    UPDATE documents
                    SET active = false
                    WHERE id = %s AND company_id = %s
                    """,
                    (doc_id, cid),
                )


def dense_search(
    query_vector: list[float],
    top_k: int,
    company_id: str | None = None,
) -> list[Document]:
    cid = company_id or settings.DEFAULT_COMPANY_ID
    warm_pg_runtime()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                  c.content,
                  c.chunk_index,
                  d.id::text AS document_id,
                  d.original_filename,
                  d.active
                FROM document_chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE d.company_id = %s AND d.active = true
                ORDER BY c.embedding <=> %s::vector
                LIMIT %s
                """,
                (cid, query_vector, top_k),
            )
            rows = cur.fetchall()

    documents: list[Document] = []
    for row in rows:
        documents.append(
            Document(
                page_content=row["content"],
                metadata={
                    "document_id": row["document_id"],
                    "original_filename": row["original_filename"],
                    "chunk_index": row["chunk_index"],
                    "active": row["active"],
                },
            )
        )
    return documents


def ping_database() -> bool:
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return True
    except Exception:
        logger.exception("PGVECTOR_PING_FAILED")
        return False
