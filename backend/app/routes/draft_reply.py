import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.observability import trace_step
from rag.config import settings
from rag.generation import generate_draft_reply

router = APIRouter()
logger = logging.getLogger("fr8labs.draft_reply")


class DraftReplyRequest(BaseModel):
    subject: str
    body: str
    sender_email: str = ""
    sender_name: str = ""


class CitationResponse(BaseModel):
    document_id: str
    original_filename: str
    chunk_index: int


class DraftReplyResponse(BaseModel):
    draft: str
    citations: list[CitationResponse]
    rerank_succeeded: bool


def _http_error_for_exception(exc: Exception) -> HTTPException:
    message = str(exc)
    lowered = message.lower()
    if isinstance(exc, ValueError):
        return HTTPException(status_code=400, detail=message)
    if "429" in message or "rate limit" in lowered or "resource exhausted" in lowered:
        return HTTPException(status_code=502, detail=message)
    return HTTPException(status_code=500, detail=message)


@router.post("", response_model=DraftReplyResponse)
def create_draft_reply(payload: DraftReplyRequest) -> DraftReplyResponse:
    if not payload.subject.strip() and not payload.body.strip():
        raise HTTPException(status_code=400, detail="Email subject or body is required.")

    logger.info(
        "DRAFT_REPLY_REQUEST | subject=%r | body_chars=%s | sender=%s <%s> | model=%s",
        payload.subject[:120],
        len(payload.body),
        payload.sender_name,
        payload.sender_email,
        settings.GENERATION_MODEL,
    )

    try:
        with trace_step(
            "draft_reply_pipeline",
            logger,
            subject_chars=len(payload.subject),
            body_chars=len(payload.body),
            generation_model=settings.GENERATION_MODEL,
        ):
            result = generate_draft_reply(payload.subject, payload.body)
    except Exception as exc:
        logger.exception("DRAFT_REPLY_FAILED | error=%s", exc)
        raise _http_error_for_exception(exc) from exc

    logger.info(
        "DRAFT_REPLY_SUCCESS | draft_chars=%s | citations=%s | rerank_succeeded=%s",
        len(result.draft_text),
        len(result.citations),
        result.rerank_succeeded,
    )

    if not result.draft_text.strip():
        raise HTTPException(
            status_code=502,
            detail="Gemini returned an empty draft. Please try regenerating.",
        )

    return DraftReplyResponse(
        draft=result.draft_text,
        citations=[
            CitationResponse(
                document_id=c.document_id,
                original_filename=c.original_filename,
                chunk_index=c.chunk_index,
            )
            for c in result.citations
        ],
        rerank_succeeded=result.rerank_succeeded,
    )
