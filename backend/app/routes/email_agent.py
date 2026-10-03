import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, field_validator

from app.observability import trace_step
from email_agent.drafts import (
    DraftRecord,
    approve_draft,
    get_draft,
    list_pending_drafts,
    send_approved_draft,
)
from email_agent.conversation import InboundConversationMessage
from email_agent.pipeline import handle_inbound_email

router = APIRouter()
logger = logging.getLogger("fr8labs.email_agent")


class CitationResponse(BaseModel):
    document_id: str
    original_filename: str
    chunk_index: int


class DraftResponse(BaseModel):
    id: str
    thread_id: str
    draft_body: str
    retrieval_status: str
    citations: list[CitationResponse]
    status: str
    created_at: datetime
    reviewed_at: datetime | None
    reviewed_by: str | None
    sent_at: datetime | None


class ApproveDraftRequest(BaseModel):
    reviewed_by: str
    draft_body: str | None = None


class SendDraftResponse(BaseModel):
    draft_id: str
    sent_body: str


class ConversationMessageIn(BaseModel):
    source_message_id: str
    body: str
    received_at: datetime | None = None

    @field_validator("source_message_id", "body")
    @classmethod
    def strip_required(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be empty")
        return stripped


class InboundEmailRequest(BaseModel):
    thread_id: str
    email_body: str
    source_message_id: str
    conversation_messages: list[ConversationMessageIn] | None = None

    @field_validator("thread_id", "email_body", "source_message_id")
    @classmethod
    def strip_required(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be empty")
        return stripped


class InboundEmailResponse(BaseModel):
    draft_id: str
    duplicate: bool = False


def _http_error_for_value_error(exc: ValueError) -> HTTPException:
    message = str(exc)
    if "not found" in message.lower():
        return HTTPException(status_code=404, detail=message)
    return HTTPException(status_code=400, detail=message)


def _to_draft_response(record: DraftRecord) -> DraftResponse:
    return DraftResponse(
        id=record.id,
        thread_id=record.thread_id,
        draft_body=record.draft_body,
        retrieval_status=record.retrieval_status,
        citations=[
            CitationResponse(
                document_id=c.document_id,
                original_filename=c.original_filename,
                chunk_index=c.chunk_index,
            )
            for c in record.citations
        ],
        status=record.status,
        created_at=record.created_at,
        reviewed_at=record.reviewed_at,
        reviewed_by=record.reviewed_by,
        sent_at=record.sent_at,
    )


@router.post("/inbound", response_model=InboundEmailResponse)
def inbound_email(payload: InboundEmailRequest):
    try:
        with trace_step(
            "email_agent_inbound",
            logger,
            thread_id=payload.thread_id,
            email_chars=len(payload.email_body),
        ):
            conversation_messages = None
            if payload.conversation_messages is not None:
                conversation_messages = [
                    InboundConversationMessage(
                        source_message_id=item.source_message_id,
                        body=item.body,
                        received_at=item.received_at,
                    )
                    for item in payload.conversation_messages
                ]
            result = handle_inbound_email(
                payload.thread_id,
                payload.email_body,
                source_message_id=payload.source_message_id,
                conversation_messages=conversation_messages,
            )
    except ValueError as exc:
        raise _http_error_for_value_error(exc) from exc
    except Exception as exc:
        logger.exception(
            "INBOUND_FAILED | thread_id=%s",
            payload.thread_id,
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return InboundEmailResponse(draft_id=result.draft_id, duplicate=result.duplicate)


@router.get("/drafts", response_model=list[DraftResponse])
def list_drafts(thread_id: str | None = Query(default=None)):
    try:
        with trace_step("list_pending_drafts", logger, thread_id=thread_id):
            records = list_pending_drafts(thread_id)
    except ValueError as exc:
        raise _http_error_for_value_error(exc) from exc
    return [_to_draft_response(r) for r in records]


@router.get("/drafts/{draft_id}", response_model=DraftResponse)
def read_draft(draft_id: str):
    try:
        with trace_step("get_draft", logger, draft_id=draft_id):
            record = get_draft(draft_id)
    except ValueError as exc:
        raise _http_error_for_value_error(exc) from exc
    return _to_draft_response(record)


@router.post("/drafts/{draft_id}/approve", response_model=DraftResponse)
def approve_draft_route(draft_id: str, payload: ApproveDraftRequest):
    try:
        with trace_step(
            "approve_draft",
            logger,
            draft_id=draft_id,
            reviewed_by=payload.reviewed_by,
            has_edit=payload.draft_body is not None,
        ):
            record = approve_draft(
                draft_id,
                payload.reviewed_by,
                draft_body=payload.draft_body,
            )
    except ValueError as exc:
        raise _http_error_for_value_error(exc) from exc
    return _to_draft_response(record)


@router.post("/drafts/{draft_id}/send", response_model=SendDraftResponse)
def send_draft_route(draft_id: str):
    try:
        with trace_step("send_approved_draft", logger, draft_id=draft_id):
            sent_body = send_approved_draft(draft_id)
    except ValueError as exc:
        raise _http_error_for_value_error(exc) from exc
    except Exception as exc:
        logger.exception("SEND_DRAFT_FAILED | draft_id=%s", draft_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return SendDraftResponse(draft_id=draft_id, sent_body=sent_body)
