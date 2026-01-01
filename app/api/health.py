from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.schemas import HealthzResponse
from app.db.session import get_db

router = APIRouter()


@router.get("/healthz", response_model=HealthzResponse)
def health_check_db(session: Session = Depends(get_db)):
    try:
        session.execute(text("SELECT 1"))
        session.execute(text("SELECT 1 FROM advertisers LIMIT 1"))
    except Exception:
        return HealthzResponse(status="error", db="unavailable")
    return HealthzResponse(status="ok", db="ok")
