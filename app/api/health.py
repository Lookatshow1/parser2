from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.get("/healthz")
def health_check_db(session: Session = Depends(get_db)):
    try:
        session.execute(text("SELECT 1"))
        session.execute(text("SELECT 1 FROM advertisers LIMIT 1"))
    except Exception:
        return {"status": "error", "db": "unavailable"}
    return {"status": "ok", "db": "ok"}
