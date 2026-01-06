from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.db.models import JobRun, JobStatus

def test_jobs_flow(client: TestClient, db: Session):
    # 1. Create demo job
    response = client.post("/api/dev/jobs/demo")
    assert response.status_code == 200
    data = response.json()
    job_id = data["id"]
    assert data["job_type"] == "dev_demo"
    assert data["status"] == "success"
    assert data["result_json"]["ok"] is True

    # 2. List jobs
    response = client.get("/api/jobs")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) > 0
    found = next((j for j in items if j["id"] == job_id), None)
    assert found is not None
    assert found["job_type"] == "dev_demo"
    assert found["status"] == "success"

    # 3. Get specific job
    response = client.get(f"/api/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["job_type"] == "dev_demo"
    assert data["status"] == "success"
    assert data["result_json"]["ok"] is True
