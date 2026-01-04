from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from app.db.models import JobStatus

class JobRunOut(BaseModel):
    id: int
    job_type: str
    status: JobStatus
    context_json: Dict[str, Any]
    result_json: Optional[Dict[str, Any]] = None
    error_text: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class JobRunListOut(BaseModel):
    items: List[JobRunOut]
