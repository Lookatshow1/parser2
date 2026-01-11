import pytest
from app.core.context import set_correlation_id, get_correlation_id
from app.db.models import SyncRun, SyncRunStatus, SyncRunType, Platform

def test_request_id_header(client):
    # 1. Without header
    resp = client.get("/api/healthz")
    assert resp.status_code == 200
    assert "X-Request-Id" in resp.headers
    cid1 = resp.headers["X-Request-Id"]
    assert len(cid1) > 0

    # 2. With header
    custom_id = "test-correlation-id-123"
    resp = client.get("/api/healthz", headers={"X-Request-Id": custom_id})
    assert resp.status_code == 200
    assert resp.headers["X-Request-Id"] == custom_id

def test_jobrun_syncrun_correlation(client, auth_headers, session, org_a, connection_yandex):
    custom_id = "sync-correlation-test"

    # Create sync run via API
    resp = client.post(
        "/api/sync-runs",
        headers={**auth_headers, "X-Request-Id": custom_id},
        json={
            "connection_id": connection_yandex.id,
            "params_json": {"date_from": "2023-01-01", "date_to": "2023-01-01"}
        }
    )
    assert resp.status_code == 200
    run_id = resp.json()["id"]

    # Check DB
    run = session.query(SyncRun).get(run_id)
    assert run is not None
    assert run.correlation_id == custom_id

def test_readyz(client, session):
    # Should be 200 if DB is up (session fixture ensures DB is up)
    resp = client.get("/api/readyz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
