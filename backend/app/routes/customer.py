from fastapi import APIRouter, HTTPException, Query

router = APIRouter()


@router.get("/lookup")
def lookup_customer(email: str = Query(...), domain: str = Query("")):
    raise HTTPException(status_code=501, detail="Not implemented — wire Fr8Labs partner lookup here.")


@router.post("")
def create_customer():
    raise HTTPException(status_code=501, detail="Not implemented — wire customer create here.")
