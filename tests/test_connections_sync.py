from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import Advertiser, JobRun, MetricSnapshot
from app.workers.sync_tasks import execute_sync_run


def test_connection_sync_creates_metrics_and_dashboard(client: TestClient, db: Session):
    advertiser = Advertiser(name="Stub Advertiser")
    db.add(advertiser)
    db.commit()
    db.refresh(advertiser)

    resp = client.post(
        "/api/connections",
        json={"platform": "stub", "credentials_json": {}, "advertiser_id": advertiser.id},
    )
    assert resp.status_code == 200
    connection_id = resp.json()["id"]

    sync_resp = client.post(
        "/api/sync-runs",
        json={
            "connection_id": connection_id,
            "params_json": {"date_from": "2023-01-01", "date_to": "2023-01-03"},
        },
    )
    assert sync_resp.status_code == 201
    run_id = sync_resp.json()["id"]

    execute_sync_run(run_id)

    metrics_count = (
        db.query(MetricSnapshot)
        .filter(MetricSnapshot.connection_id == connection_id)
        .count()
    )
    assert metrics_count == 6

    job = (
        db.query(JobRun)
        .filter(JobRun.connection_id == connection_id)
        .order_by(JobRun.id.desc())
        .first()
    )
    assert job is not None
    assert job.status.value == "success"

    dashboard_resp = client.get(
        "/api/dashboard/summary",
        params={
            "connection_id": connection_id,
            "date_from": "2023-01-01",
            "date_to": "2023-01-03",
        },
    )
    assert dashboard_resp.status_code == 200
    data = dashboard_resp.json()
    assert data["totals"]["impressions"] == 600
    assert data["totals"]["clicks"] == 60
    assert data["totals"]["spend"] == 1500
