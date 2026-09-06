# Fr8Labs Outlook Add-in — Backend

Python API for the Outlook add-in (`../frontend`) plus a **RAG document indexing pipeline** (`rag/`).

## Setup

Requires **Python 3.11+**.

```bash
cd backend
py -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env
```

Fill in at minimum `GOOGLE_API_KEY`, `QDRANT_URL`, and `COHERE_API_KEY` in `.env`.

## FastAPI server

```bash
python -m uvicorn app.main:app --reload --port 4000
```

API docs: http://localhost:4000/docs

### Endpoints (stubs)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Health check |
| POST | `/api/draft-reply` | AI draft reply |
| POST | `/api/quote/parse` | Parse email → quote |
| POST | `/api/quote/approve` | Create quote in Fr8Labs |
| GET | `/api/customer/lookup` | Verify customer |
| POST | `/api/customer` | Create customer |

### Admin document API

Internal endpoints for the document admin UI (browser page at `../frontend/admin.html`). Thin wrappers around the existing RAG pipeline — no duplicated indexing logic.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/admin/documents/supported-types` | List allowed file extensions |
| POST | `/api/admin/documents/upload` | Upload + index a document (synchronous) |
| GET | `/api/admin/documents` | List indexed documents |
| POST | `/api/admin/documents/{document_id}/supersede` | Mark document superseded |
| GET | `/api/admin/search-preview?q=...&top_k=5` | Hybrid search preview |

**Upload validation:** extension must be in `SUPPORTED_EXTENSIONS` (`.pdf`, `.docx`, `.txt`); max size `MAX_UPLOAD_BYTES` (default 20 MB). Temp upload files are deleted after indexing.

**Auth gap:** These endpoints are currently **unauthenticated**, like all other API routes. Do not expose the backend publicly without adding auth.

---

## RAG indexing pipeline

Indexes uploaded documents into Qdrant with **hybrid dense (Gemini) + sparse (BM25)** vectors. Sparse BM25 runs fully offline — no HuggingFace model downloads. Qdrant applies IDF weighting server-side on the `sparse` vector.

### Qdrant setup

**Local Docker (recommended for dev):**

```bash
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

Set `QDRANT_URL=http://localhost:6333` in `.env` (no API key needed).

**Qdrant Cloud:** use your cluster URL and API key from the Qdrant dashboard.

Requires Qdrant **v1.10+** for hybrid search.

### Ingest a document

```bash
cd backend
python ingest.py path/to/document.pdf
```

Supported types: `.pdf`, `.docx`, `.txt`

### List / supersede documents

No separate registry DB — document metadata lives in Qdrant payloads:

```bash
python ingest.py --list
python ingest.py --supersede <document_id>
```

`--list` scrolls Qdrant grouped by `document_id`.  
`--supersede` sets `active=false` on all chunks then deletes them.

### Rate limits (Gemini free tier)

Dense embeddings use `gemini-embedding-001` in batches of 5 with a delay between batches and exponential backoff on 429 errors. Large documents will be **slow but should complete** — do not interrupt mid-ingest.

### Package layout

```
rag/
  config.py           # env vars (validated at import)
  document_store.py   # raw file save + SHA-256
  loaders.py          # PDF/DOCX/TXT loaders
  chunking.py         # fixed-size splitter (swap point for v2)
  embeddings.py       # Gemini dense + local BM25 sparse (no HuggingFace)
  bm25_sparse.py      # offline BM25 sparse vectors for Qdrant IDF
  qdrant_store.py     # collection, list, supersede, payload indexes
  ingest.py           # ingest_file orchestration
  retrieval.py        # sanitize + hybrid search (active=true filter)
  reranking.py        # Cohere rerank with Qdrant-order fallback
  generation.py       # prompt building + Gemini draft reply
  models.py           # UploadedFile, Citation, DraftReplyResult
  retry.py            # shared Gemini rate-limit backoff
ingest.py             # indexing CLI entry point
generate_draft_reply.py  # draft-reply CLI entry point
document_store/raw/   # uploaded originals (gitignored)
```

### Indexing non-goals

- No structure-aware chunking (fixed-size only)
- No deduplication logic (content hash stored for future use)

Use the **admin UI** (`../frontend/admin.html`) or CLI (`ingest.py`) to index documents.

---

## RAG retrieval + draft reply

Query-time pipeline for the **AI Draft Reply** button. Reads from the same Qdrant collection the indexing pipeline writes to — no duplicate storage.

### Flow

1. Sanitize incoming email (strip HTML, cap length)
2. **Hybrid search** in Qdrant (dense Gemini + sparse BM25, RRF fusion) — top 30 candidates, filtered to `metadata.active=true` at query time
3. **Cohere Rerank** narrows to top 5 chunks
4. **Gemini** generates a professional reply draft grounded in retrieved context

### Generate a draft from the CLI

```bash
cd backend
python generate_draft_reply.py "Transit time inquiry" "How long does shipping from Mumbai to Singapore take?"
```

Output includes the draft text, citation list (`document_id`, `original_filename`, `chunk_index`), and whether Cohere reranking succeeded.

### Active-chunk filtering

Superseded documents are marked `active=false` during ingestion (`ingest.py --supersede`). Retrieval enforces `active=true` as a **Qdrant payload filter** on every search — superseded chunks never surface, even if still present before deletion completes.

Payload indexes on `metadata.document_id` (keyword) and `metadata.active` (bool) are created automatically on first query if missing (required for Qdrant Cloud strict mode).

### Cohere rerank fallback

If the Cohere rerank call fails (rate limit, network error, etc.), the pipeline logs a warning and uses the Qdrant hybrid-fused order instead. The draft still generates — slightly less precise retrieval beats a broken button. The `rerank_succeeded` flag in the result indicates which path was used.

### Prompt-injection defense

The generation system prompt treats the incoming email as **untrusted data**. The model is instructed to draft a reply based on the email content and retrieved policy chunks, but to ignore any embedded instructions in the email body (e.g. "ignore previous instructions", "reply saying X is approved"). Retrieved context chunks are framed as trusted reference material.

### Rate limits

Query embedding and generation both use the same exponential backoff on Gemini 429 errors as the indexing pipeline. Cohere has its own limits; failures fall back gracefully.

### Tests

```bash
cd backend
pytest tests/ -v
```

All external APIs (Qdrant, Cohere, Gemini) are mocked — no network calls required.

### Draft-reply non-goals

- No auto-send — returns draft text + citations only; sending is manual in Outlook
- No FastAPI route wiring yet (`/api/draft-reply` remains a stub)
- No Create Quote or Customer flows
