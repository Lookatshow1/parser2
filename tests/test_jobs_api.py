from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.db.models import Advertiser, Connection, Platform
from app.jobs.service import create_job

def test_jobs_flow(client: TestClient, db: Session):
    # 1. Create demo job
    response = client.post("/api/dev/jobs/demo")
    assert response.status_code == 200
    data = response.json()
    job_id = data["id"]
    assert data["job_type"] == "dev_demo"
    assert data["status"] == "success"
    assert data["result_json"]["ok"] is True

    advertiser = Advertiser(name="Jobs Advertiser")
    db.add(advertiser)
    db.commit()
    db.refresh(advertiser)

    connection = Connection(
        organization_id=1,
        advertiser_id=advertiser.id,
        platform=Platform.stub,
        name="Jobs Connection",
        credentials_json={}
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)

    filtered_job = create_job(
        db,
        job_type="connection_sync",
        context={"connection_id": connection.id},
        organization_id=1,
        connection_id=connection.id,
    )

    # 2. List jobs
    response = client.get("/api/jobs")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) > 0
    found = next((j for j in items if j["id"] == job_id), None)
    assert found is not None
    assert found["job_type"] == "dev_demo"
    assert found["status"] == "success"

    response = client.get("/api/jobs", params={"connection_id": connection.id})
    assert response.status_code == 200
    items = response.json()["items"]
    ids = {item["id"] for item in items}
    assert filtered_job.id in ids

    response = client.get("/api/job-runs", params={"connection_id": connection.id})
    assert response.status_code == 200
    items = response.json()["items"]
    ids = {item["id"] for item in items}
    assert filtered_job.id in ids

    # 3. Get specific job
    response = client.get(f"/api/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["job_type"] == "dev_demo"
    assert data["status"] == "success"
    assert data["result_json"]["ok"] is True

    response = client.get(f"/api/job-runs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
