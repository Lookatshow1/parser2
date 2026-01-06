from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import Advertiser
from app.workers.sync_tasks import execute_sync_run


def test_dashboard_efficiency_calcs(client: TestClient, db: Session, auth_context):
    advertiser = Advertiser(name="Efficiency Advertiser")
    db.add(advertiser)
    db.commit()
    db.refresh(advertiser)

    resp = client.post(
        "/api/connections",
        json={"platform": "stub", "credentials_json": {}, "advertiser_id": advertiser.id},
        headers=auth_context["headers"],
    )
    assert resp.status_code == 200
    connection_id = resp.json()["id"]

    sync_resp = client.post(
        "/api/sync-runs",
        json={
            "connection_id": connection_id,
            "params_json": {"date_from": "2023-01-01", "date_to": "2023-01-03"},
        },
        headers=auth_context["headers"],
    )
    assert sync_resp.status_code == 201
    run_id = sync_resp.json()["id"]

    execute_sync_run(run_id)

    dashboard_resp = client.get(
        "/api/dashboard/summary",
        params={
            "connection_id": connection_id,
            "date_from": "2023-01-01",
            "date_to": "2023-01-03",
        },
        headers=auth_context["headers"],
    )
    assert dashboard_resp.status_code == 200
    totals = dashboard_resp.json()["totals"]
    assert totals["ctr"] == 0.1
    assert totals["cpc"] == 25.0
    assert totals["cpm"] == 2500.0
    assert totals["cpa"] is None
