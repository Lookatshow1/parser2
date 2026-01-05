import os
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.db.models import Connection, CampaignPlan, Experiment, Platform, SyncRun, SyncRunStatus, SyncRunType, ExperimentCampaign, MetricSnapshot

def test_ozon_full_sync_writes_campaigns_and_metrics(client: TestClient, db: Session):
    # 1. Setup
    os.environ["OZON_PERF_MOCK"] = "1"

    conn = Connection(platform=Platform.ozon, name="Test Ozon", credentials_json={"client_id": "fake", "client_secret": "fake"})
    db.add(conn)
    db.commit()

    plan = CampaignPlan(name="Test Plan Ozon", platform=Platform.ozon, advertiser_id=1, connection_id=conn.id)
    db.add(plan)
    db.commit()

    exp = Experiment(plan_id=plan.id, status="running")
    db.add(exp)
    db.commit()

    # 2. Trigger sync
    payload = {
        "platform": "ozon",
        "run_type": "full",
        "date_from": "2023-01-01",
        "date_to": "2023-01-02"
    }
    resp = client.post(f"/api/experiments/{exp.id}/sync", json=payload)
    assert resp.status_code == 200
    run_id = resp.json()["id"]

    # In eager mode, task runs synchronously.

    # 3. Verify SyncRun status
    run = db.query(SyncRun).get(run_id)
    assert run.status == SyncRunStatus.success

    # 4. Verify campaigns
    campaigns = db.query(ExperimentCampaign).filter(ExperimentCampaign.experiment_id == exp.id).all()
    assert len(campaigns) == 2
    assert campaigns[0].platform == Platform.ozon

    # 5. Verify metrics
    metrics_count = db.query(MetricSnapshot).filter(MetricSnapshot.experiment_id == exp.id).count()
    # 2 campaigns * 2 days = 4 snapshots
    assert metrics_count == 4

    # 6. Test Summary
    summary_resp = client.get(f"/api/experiments/{exp.id}/summary", params={
        "platform": "ozon", "date_from": "2023-01-01", "date_to": "2023-01-02"
    })
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    # Mock data: 2 days, 2 campaigns
    # Impressions: (510+520) * 2 = 2060
    # Clicks: (51+52) * 2 = 206
    # Spend: 1000 * 2 * 2 = 4000
    assert summary["impressions"] == 2060
    assert summary["clicks"] == 206
    assert summary["spend"] == 4000
    assert summary["cpc"] == 4000 / 206

    # 7. Test Metrics Group by Day
    metrics_resp = client.get(f"/api/experiments/{exp.id}/metrics", params={
        "platform": "ozon", "date_from": "2023-01-01", "date_to": "2023-01-01", "group_by": "day"
    })
    assert metrics_resp.status_code == 200
    metrics_data = metrics_resp.json()["items"]
    assert len(metrics_data) == 1
    assert metrics_data[0]["impressions"] == 1030 # 510 + 520

    del os.environ["OZON_PERF_MOCK"]
