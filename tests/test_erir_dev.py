from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import ErirEvent, ErirStatus, JobRun, JobStatus
from app.workers.erir_tasks import execute_erir_register


def test_erir_dev_register(client: TestClient, db: Session, auth_context):
    resp = client.post(
        "/api/erir/dev/register",
        json={"payload_json": {"note": "test"}},
        headers=auth_context["headers"],
    )
    assert resp.status_code == 200
    data = resp.json()
    event_id = data["erir_event_id"]
    job_id = data["job_run_id"]

    execute_erir_register(event_id, job_id)

    event = db.query(ErirEvent).get(event_id)
    assert event.status == ErirStatus.success
    assert event.result_json is not None

    job = db.query(JobRun).get(job_id)
    assert job.status == JobStatus.success
