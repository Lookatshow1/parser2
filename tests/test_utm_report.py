from datetime import datetime, timezone
from uuid import uuid4

from app.db.models import AdCampaign, CampaignPlan, Platform


def test_utm_report_campaign_grouping(client, auth_headers, db_session, org_a):
    plan = CampaignPlan(
        organization_id=org_a.id,
        advertiser_id=1,
        name="UTM Plan",
        platform=Platform.yandex,
        internal_code="plan-utm-123",
    )
    db_session.add(plan)
    db_session.commit()

    payload = {
        "event_id": str(uuid4()),
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "landing_url": "https://example.com/landing",
        "utm_campaign": "plan-utm-123",
        "utm_source": "yandex",
    }
    resp_event = client.post("/api/events/lead", json=payload)
    assert resp_event.status_code == 200

    resp_report = client.get("/api/utm/report?group_by=campaign", headers=auth_headers)
    assert resp_report.status_code == 200
    payload = resp_report.json()
    items = payload["items"]
    totals = payload["totals"]

    row = next((item for item in items if item["utm_campaign"] == "plan-utm-123"), None)
    assert row is not None
    assert row["leads"] == 1
    assert row["purchases"] == 0
    assert row["total"] == 1
    assert totals["leads"] == 1
    assert totals["purchases"] == 0
    assert totals["total"] == 1


def test_utm_report_unlinked_campaign(client, auth_headers, db_session, org_a, connection_yandex):
    campaign = AdCampaign(
        organization_id=org_a.id,
        connection_id=connection_yandex.id,
        platform=Platform.yandex,
        external_id="ext-campaign-777",
        name="Campaign 777",
    )
    db_session.add(campaign)
    db_session.commit()

    payload = {
        "event_id": str(uuid4()),
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "landing_url": "https://example.com/landing",
        "utm_campaign": "ext-campaign-777",
        "utm_source": "yandex",
    }
    resp_event = client.post("/api/events/lead", json=payload)
    assert resp_event.status_code == 200

    resp_linked_only = client.get("/api/utm/report?group_by=campaign", headers=auth_headers)
    assert resp_linked_only.status_code == 200
    linked_payload = resp_linked_only.json()
    items_linked = linked_payload["items"]
    assert not any(item["utm_campaign"] == "ext-campaign-777" for item in items_linked)
    assert linked_payload["totals"]["total"] == 0

    resp_report = client.get(
        "/api/utm/report?group_by=campaign&include_unlinked=true",
        headers=auth_headers,
    )
    assert resp_report.status_code == 200
    payload = resp_report.json()
    items = payload["items"]
    row = next((item for item in items if item["utm_campaign"] == "ext-campaign-777"), None)
    assert row is not None
    assert row["leads"] == 1
    assert row["total"] == 1
    assert payload["totals"]["leads"] == 1
    assert payload["totals"]["total"] == 1
