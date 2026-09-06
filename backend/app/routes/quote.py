from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class QuoteParseRequest(BaseModel):
    subject: str
    body: str
    sender_email: str = ""


@router.post("/parse")
def parse_quote(payload: QuoteParseRequest):
    raise HTTPException(status_code=501, detail="Not implemented — wire quote parsing here.")


@router.post("/approve")
def approve_quote():
    raise HTTPException(status_code=501, detail="Not implemented — wire Fr8Labs quote create here.")
