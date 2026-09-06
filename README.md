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
