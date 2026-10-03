-- Company RAG: Neon PostgreSQL + pgvector (dense-only)
-- Run once in Neon SQL Editor, or rely on rag/pg_store.ensure_schema() at startup.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

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
  embedding vector(3072) NOT NULL,
  UNIQUE (document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_documents_company_active
  ON documents (company_id, active);

CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id
  ON document_chunks (document_id);
