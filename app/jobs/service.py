from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.models import JobRun, JobStatus

SENSITIVE_KEYS = {
    "token", "access_token", "refresh_token", "client_secret", "secret", "password", "api_key"
}

def sanitize_payload(data: dict | None) -> dict:
    if not data:
        return {}

    cleaned = {}
    for k, v in data.items():
        if k.lower() in SENSITIVE_KEYS:
            cleaned[k] = "***"
        elif isinstance(v, dict):
            cleaned[k] = sanitize_payload(v)
        elif isinstance(v, list):
            cleaned[k] = [sanitize_payload(i) if isinstance(i, dict) else i for i in v]
        else:
            cleaned[k] = v
    return cleaned

def create_job(
    db: Session,
    job_type: str,
    context: dict,
    organization_id: int | None = None,
    connection_id: int | None = None,
) -> JobRun:
    job = JobRun(
        organization_id=organization_id,
        connection_id=connection_id,
        job_type=job_type,
        status=JobStatus.queued,
        context_json=sanitize_payload(context)
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

def mark_running(db: Session, job_id: int) -> JobRun:
    job = db.query(JobRun).get(job_id)
    if job:
        job.status = JobStatus.running
        job.started_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(job)
    return job

def mark_succeeded(db: Session, job_id: int, result: dict) -> JobRun:
    job = db.query(JobRun).get(job_id)
    if job:
        job.status = JobStatus.succeeded
        job.finished_at = datetime.now(timezone.utc)
        job.result_json = sanitize_payload(result)
        db.commit()
        db.refresh(job)
    return job

def mark_failed(db: Session, job_id: int, error_text: str) -> JobRun:
    job = db.query(JobRun).get(job_id)
    if job:
        job.status = JobStatus.failed
        job.finished_at = datetime.now(timezone.utc)
        job.error_text = error_text
        db.commit()
        db.refresh(job)
    return job
