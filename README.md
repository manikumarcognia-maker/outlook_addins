# Fr8Labs Outlook Add-in

Monorepo for the Fr8Labs Outlook integration.

```
Addins/
  frontend/    Outlook add-in (React + Vite + manifest)
  backend/     API server (FastAPI / Python)
  docs/        Integration plan & architecture
```

## Quick start

**Frontend (Outlook add-in)**

```bash
cd frontend
npm install
npm run certs   # once
npm run dev     # https://localhost:3000
```

Sideload `frontend/manifest.xml` in Outlook.

**Document admin (internal)**

Browser-only page for uploading and managing indexed documents (not part of the Outlook task pane):

```bash
# Start backend first (port 4000), then:
cd frontend
npm run dev
# Open https://localhost:3000/admin.html
```

Copy `frontend/.env.example` to `frontend/.env` if the API is not on `http://localhost:4000`.

**Auth gap:** The admin page and `/api/admin/*` endpoints have no authentication yet. Restrict network access in production.

**Backend (FastAPI + RAG indexing)**

```bash
cd backend
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 4000
```

RAG document indexing (CLI): see [backend/README.md](backend/README.md).

## Git / Replit deploy

Do **not** commit `backend/.env`, `frontend/.env`, `node_modules`, or `.venv`. Those are gitignored.

Remote already pointed at: `https://github.com/manikumarcognia-maker/outlook_addins.git`

```bash
git add .
git status   # confirm no .env files
git commit -m "Add Outlook add-in UI, FastAPI RAG backend, and Replit deploy files."
git push -u origin addins_V1
```

### Replit

1. Create a Repl from that GitHub repo (or import the same branch).
2. Use **Autoscale** or a reserved VM — RAG + Node build needs more RAM than a free Repl.
3. Add **Secrets** (not a committed `.env`):

| Secret | Required |
|---|---|
| `GOOGLE_API_KEY` | yes |
| `QDRANT_URL` | yes |
| `QDRANT_API_KEY` | yes for Qdrant Cloud |
| `COHERE_API_KEY` | yes |
| `QDRANT_COLLECTION` | optional (`fr8labs_production`) |
| `GENERATION_MODEL` | optional (`gemini-3.5-flash-lite`) |
| `ADDIN_PUBLIC_URL` | yes after first deploy: `https://<your-repl>.replit.app` |

4. Run **Build** then **Run**. The API and the built add-in are served from one process (`$PORT`).
5. Check `https://<your-repl>/health`.
6. Sideload Outlook from `https://<your-repl>/manifest.xml` (URLs are rewritten from localhost to `ADDIN_PUBLIC_URL`).
7. Admin UI: `https://<your-repl>/admin.html` — still **unauthenticated**; do not leave it public without auth.

Leave `VITE_API_BASE_URL` empty so the UI calls `/api` on the same host.

Local Outlook testing still uses `npm run dev` on `https://localhost:3000` and `frontend/manifest.xml`.
