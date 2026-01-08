from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.workers.sync_tasks import execute_sync_run


def test_metrics_timeseries_for_mock_connection(client: TestClient, db: Session, auth_context):
    resp = client.post(
        "/api/connections",
        json={"platform": "yandex", "credentials_json": {"mock": True}},
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

    ts_resp = client.get(
        "/api/metrics/timeseries",
        params={"date_from": "2023-01-01", "date_to": "2023-01-03", "connection_ids": str(connection_id)},
        headers=auth_context["headers"],
    )
    assert ts_resp.status_code == 200
    data = ts_resp.json()
    assert "series" in data
    assert data["series"]["spend"]
    assert data["totals"]["spend"] > 0

    org_b = client.post("/api/orgs", json={"name": "Org B"}, headers=auth_context["headers"])
    assert org_b.status_code == 201
    org_b_id = org_b.json()["id"]
    headers_b = {
        **auth_context["headers"],
        "X-Org-Id": str(org_b_id),
    }
    ts_other = client.get(
        "/api/metrics/timeseries",
        params={"date_from": "2023-01-01", "date_to": "2023-01-03", "connection_ids": str(connection_id)},
        headers=headers_b,
    )
    assert ts_other.status_code == 404
