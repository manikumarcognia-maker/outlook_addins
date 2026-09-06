import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from app.observability import configure_observability, trace_step
from app.routes import admin_documents, customer, draft_reply, quote
from rag.config import settings
from rag.runtime import warm_rag_runtime

REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ROOT = REPO_ROOT / "frontend"
FRONTEND_DIST = FRONTEND_ROOT / "dist"

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
    allow_credentials=True,
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
        logger.info(
            "HTTP_RESPONSE | %s %s | status=%s",
            request.method,
            request.url.path,
            response.status_code,
        )
        return response


app.include_router(draft_reply.router, prefix="/api/draft-reply", tags=["draft-reply"])
app.include_router(quote.router, prefix="/api/quote", tags=["quote"])
app.include_router(customer.router, prefix="/api/customer", tags=["customer"])
app.include_router(admin_documents.router, prefix="/api/admin", tags=["admin"])


@app.get("/health")
def health():
    return {"ok": True, "service": "fr8labs-outlook-addin-backend"}


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
    return Response(content=xml, media_type="application/xml")


if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
