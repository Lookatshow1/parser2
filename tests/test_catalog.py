import pytest
from app.db.models import AdCampaign, AdAdGroup, AdAd, OrgUtmSettings
from app.services.ad_catalog_service import refresh_catalog_for_connection

def test_catalog_refresh(session, connection_yandex, metric_snapshot_factory):
    # Create snapshots
    metric_snapshot_factory(
        connection=connection_yandex,
        campaign_external_id="c1",
        ad_group_external_id="g1",
        ad_external_id="a1"
    )
    metric_snapshot_factory(
        connection=connection_yandex,
        campaign_external_id="c1",
        ad_group_external_id="g2",
        ad_external_id="a2"
    )

    # Refresh
    stats = refresh_catalog_for_connection(session, connection_yandex.id)
    assert stats["campaigns"] == 1
    assert stats["groups"] == 2
    assert stats["ads"] == 2

    # Check DB
    c = session.query(AdCampaign).filter_by(external_id="c1").first()
    assert c is not None
    assert c.name == "Кампания c1"

    g = session.query(AdAdGroup).filter_by(external_id="g1").first()
    assert g is not None
    assert g.campaign_external_id == "c1"

    a = session.query(AdAd).filter_by(external_id="a1").first()
    assert a is not None
    assert a.ad_group_external_id == "g1"

def test_catalog_api(client, auth_headers, connection_yandex, session, metric_snapshot_factory):
    # Seed catalog
    metric_snapshot_factory(
        connection=connection_yandex,
        campaign_external_id="c1",
        ad_group_external_id="g1",
        ad_external_id="a1"
    )
    refresh_catalog_for_connection(session, connection_yandex.id)

    # List campaigns
    resp = client.get(f"/api/connections/{connection_yandex.id}/campaigns", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    assert data[0]["external_id"] == "c1"

def test_utm_build(client, auth_headers, org_a):
    # Default settings
    resp = client.post(
        "/api/utm/build",
        headers=auth_headers,
        json={
            "url": "https://example.com",
            "platform": "yandex",
            "campaign_external_id": "123",
            "ad_external_id": "456"
        }
    )
    assert resp.status_code == 200
    url = resp.json()["final_url"]
    assert "utm_source=yandex" in url
    assert "utm_campaign=123" in url
    assert "utm_content=456" in url

def test_utm_settings_update(client, auth_headers, org_a):
    # Update settings
    resp = client.put(
        "/api/settings/utm",
        headers=auth_headers,
        json={"utm_source": "custom_source"}
    )
    assert resp.status_code == 200
    assert resp.json()["utm_source"] == "custom_source"

    # Build with new settings
    resp = client.post(
        "/api/utm/build",
        headers=auth_headers,
        json={
            "url": "https://example.com",
            "platform": "yandex"
        }
    )
    url = resp.json()["final_url"]
    assert "utm_source=custom_source" in url
