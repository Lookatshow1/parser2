from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import SyncRunResponse
from app.db.models import SyncRun
from app.db.session import get_db

router = APIRouter(prefix="/sync-runs", tags=["sync-runs"])

@router.get("/{run_id}", response_model=SyncRunResponse)
def get_sync_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(SyncRun).get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="SyncRun not found")
    return run
