import os
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.db.models import Connection, CampaignPlan, Experiment, Platform, MetricSnapshot, ExperimentCampaign

def test_dashboard_read_api(client: TestClient, db: Session):
    # 1. Setup Data
    conn = Connection(platform=Platform.yandex, name="Test Yandex", credentials_json={"token": "fake"})
    db.add(conn)
    db.commit()

    plan = CampaignPlan(name="Test Plan", platform=Platform.yandex, advertiser_id=1, connection_id=conn.id)
    db.add(plan)
    db.commit()

    exp = Experiment(plan_id=plan.id, status="running")
    db.add(exp)
    db.commit()

    # Add campaigns
    c1 = ExperimentCampaign(experiment_id=exp.id, platform=Platform.yandex, campaign_external_id="111")
    c2 = ExperimentCampaign(experiment_id=exp.id, platform=Platform.yandex, campaign_external_id="222")
    db.add_all([c1, c2])

    # Add metrics
    # Day 1
    m1 = MetricSnapshot(
        date=date(2023, 1, 1), platform=Platform.yandex, campaign_external_id="111",
        experiment_id=exp.id, plan_id=plan.id, connection_id=conn.id,
        impressions=1000, clicks=50, spend=500
    )
    m2 = MetricSnapshot(
        date=date(2023, 1, 1), platform=Platform.yandex, campaign_external_id="222",
        experiment_id=exp.id, plan_id=plan.id, connection_id=conn.id,
        impressions=2000, clicks=80, spend=800
    )
    # Day 2
    m3 = MetricSnapshot(
        date=date(2023, 1, 2), platform=Platform.yandex, campaign_external_id="111",
        experiment_id=exp.id, plan_id=plan.id, connection_id=conn.id,
        impressions=1500, clicks=60, spend=600
    )
    db.add_all([m1, m2, m3])
    db.commit()

    # 2. Test Campaigns API
    resp = client.get(f"/api/experiments/{exp.id}/campaigns")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    # 3. Test Metrics API (group by day)
    resp = client.get(f"/api/experiments/{exp.id}/metrics", params={
        "date_from": "2023-01-01", "date_to": "2023-01-02", "group_by": "day"
    })
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 2
    # Day 1 total: 1000+2000=3000 imp, 50+80=130 clicks
    assert items[0]["date"] == "2023-01-01"
    assert items[0]["impressions"] == 3000
    assert items[0]["clicks"] == 130

    # 4. Test Metrics API (group by campaign)
    resp = client.get(f"/api/experiments/{exp.id}/metrics", params={
        "date_from": "2023-01-01", "date_to": "2023-01-02", "group_by": "campaign"
    })
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 2
    # Campaign 111 total: 1000+1500=2500 imp
    c111 = next(i for i in items if i["campaign_external_id"] == "111")
    assert c111["impressions"] == 2500

    # 5. Test Summary API
    resp = client.get(f"/api/experiments/{exp.id}/summary", params={
        "date_from": "2023-01-01", "date_to": "2023-01-02"
    })
    assert resp.status_code == 200
    data = resp.json()
    # Total: 3000 (day1) + 1500 (day2 c111) = 4500
    assert data["impressions"] == 4500
    assert data["clicks"] == 190 # 130 + 60
    assert data["spend"] == 1900 # 1300 + 600

    # Check calculated fields
    # CTR = 190 / 4500 * 100 = 4.22%
    assert 4.2 < data["ctr"] < 4.3
    # CPC = 1900 / 190 = 10.0
    assert data["cpc"] == 10.0
    # CPM = 1900 / 4500 * 1000 = 422.22
    assert 422 < data["cpm"] < 423
