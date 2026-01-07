from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import Advertiser
from app.workers.sync_tasks import execute_sync_run
from app.connectors.stub import StubConnector


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
    stub_metrics = StubConnector().fetch_metrics(
        date_from=date(2023, 1, 1),
        date_to=date(2023, 1, 3),
        connection_id=connection_id,
    )
    impressions = sum(item["impressions"] for item in stub_metrics)
    clicks = sum(item["clicks"] for item in stub_metrics)
    spend = sum(item["spend"] for item in stub_metrics)
    purchases = sum(item["purchases"] for item in stub_metrics)
    expected_ctr = round(clicks / impressions, 4)
    expected_cpc = round(spend / clicks, 2)
    expected_cpm = round((spend * 1000) / impressions, 2)
    expected_cpa = round(spend / purchases, 2) if purchases else None
    assert totals["ctr"] == expected_ctr
    assert totals["cpc"] == expected_cpc
    assert totals["cpm"] == expected_cpm
    assert totals["cpa"] == expected_cpa
    assert totals["roas"] == 0.0
