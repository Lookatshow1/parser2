import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api.deps import get_current_org, get_current_user
from app.db.session import get_db
from app.db.models import JobRun, JobStatus, Organization, User
from app.jobs.schemas import JobRunOut, JobRunListOut
from app.jobs.service import create_job, mark_running, mark_succeeded, mark_failed

router = APIRouter()

@router.get("/jobs", response_model=JobRunListOut)
@router.get("/job-runs", response_model=JobRunListOut)
def list_jobs(
    limit: int = Query(50, le=200),
    status: Optional[JobStatus] = None,
    job_type: Optional[str] = None,
    organization_id: Optional[int] = Query(None, ge=1),
    connection_id: Optional[int] = Query(None, ge=1),
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
):
    query = db.query(JobRun).filter(JobRun.organization_id == org.id)

    if status:
        query = query.filter(JobRun.status == status)
    if job_type:
        query = query.filter(JobRun.job_type == job_type)
    if organization_id:
        query = query.filter(JobRun.organization_id == organization_id)
    if connection_id:
        query = query.filter(JobRun.connection_id == connection_id)

    jobs = query.order_by(desc(JobRun.created_at)).limit(limit).all()
    return {"items": jobs}

@router.get("/jobs/{job_id}", response_model=JobRunOut)
@router.get("/job-runs/{job_id}", response_model=JobRunOut)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
):
    job = db.query(JobRun).filter(JobRun.id == job_id, JobRun.organization_id == org.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.post("/dev/jobs/demo", response_model=JobRunOut)
def create_demo_job(
    db: Session = Depends(get_db),
    org: Organization = Depends(get_current_org),
    user: User = Depends(get_current_user),
):
    # 1. Create job
    job = create_job(db, job_type="dev_demo", context={"note": "demo"}, organization_id=org.id)

    # 2. Mark running
    mark_running(db, job.id)

    # 3. Do some work
    _ = json.loads(json.dumps({"test": "data"}))

    # 4. Mark succeeded
    job = mark_succeeded(db, job.id, result={"ok": True})

    return job
