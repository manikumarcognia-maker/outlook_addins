import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from app.observability import configure_observability, trace_step
from app.routes import admin_documents, customer, draft_reply, email_agent, quote
from rag.config import settings
from rag.pg_store import ping_database
from rag.runtime import warm_rag_runtime

REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ROOT = REPO_ROOT / "frontend"
FRONTEND_DIST = FRONTEND_ROOT / "dist"
PUBLIC_ASSETS = FRONTEND_ROOT / "public" / "assets"
DIST_ASSETS = FRONTEND_DIST / "assets"

logger = configure_observability(settings.LOG_FILE, settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Backend starting | generation_model=%s", settings.GENERATION_MODEL)
    warm_rag_runtime()
    yield
    logger.info("Backend shutting down")


app = FastAPI(title="Fr8Labs Outlook Add-in API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    with trace_step(
        "http_request",
        logger,
        method=request.method,
        path=request.url.path,
    ):
        response = await call_next(request)
        # Outlook loads the task pane in an iframe on office.com.
        response.headers["Content-Security-Policy"] = "frame-ancestors *"
        response.headers["Access-Control-Allow-Origin"] = "*"
        if "x-frame-options" in response.headers:
            del response.headers["x-frame-options"]
        logger.info(
            "HTTP_RESPONSE | %s %s | status=%s",
            request.method,
            request.url.path,
            response.status_code,
        )
        return response


app.include_router(draft_reply.router, prefix="/api/draft-reply", tags=["draft-reply"])
app.include_router(email_agent.router, prefix="/api/email-agent", tags=["email-agent"])
app.include_router(quote.router, prefix="/api/quote", tags=["quote"])
app.include_router(customer.router, prefix="/api/customer", tags=["customer"])
app.include_router(admin_documents.router, prefix="/api/admin", tags=["admin"])


@app.get("/health")
def health():
    db_ok = ping_database()
    return {
        "ok": db_ok,
        "service": "fr8labs-outlook-addin-backend",
        "database": "ok" if db_ok else "unavailable",
    }


def _addin_public_url() -> str | None:
    explicit = os.environ.get("ADDIN_PUBLIC_URL", "").strip().rstrip("/")
    if explicit:
        return explicit
    domain = os.environ.get("REPLIT_DEV_DOMAIN", "").strip()
    if domain:
        return f"https://{domain}"
    domains = os.environ.get("REPLIT_DOMAINS", "").split(",")
    first = domains[0].strip() if domains else ""
    if first:
        return f"https://{first}"
    return None


@app.get("/manifest.xml")
def office_manifest():
    manifest_path = FRONTEND_ROOT / "manifest.xml"
    xml = manifest_path.read_text(encoding="utf-8")
    public_url = _addin_public_url()
    if public_url:
        xml = xml.replace("https://localhost:3000", public_url)
    return Response(
        content=xml,
        media_type="text/xml",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/assets/{filename}")
def serve_asset(filename: str):
    if "/" in filename or "\\" in filename or filename.startswith("."):
        raise HTTPException(status_code=404, detail="Not found")
    for folder in (PUBLIC_ASSETS, DIST_ASSETS):
        path = folder / filename
        if path.is_file():
            media = "image/png" if filename.endswith(".png") else None
            return FileResponse(path, media_type=media)
    raise HTTPException(status_code=404, detail="Not found")


if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
