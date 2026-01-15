from app.db.models import AdCampaign, AdAdGroup, AdAd, Platform
from app.services.auth_service import create_access_token


def test_utm_reconcile_updates_urls(client, db, auth_headers, connection_yandex, org_a, user_b):
    camp = AdCampaign(
        organization_id=org_a.id,
        connection_id=connection_yandex.id,
        platform=Platform.yandex,
        external_id="c1",
        name="Кампания 1",
    )
    group = AdAdGroup(
        organization_id=org_a.id,
        connection_id=connection_yandex.id,
        platform=Platform.yandex,
        external_id="g1",
        campaign_external_id="c1",
        name="Группа 1",
    )
    ad_ok = AdAd(
        organization_id=org_a.id,
        connection_id=connection_yandex.id,
        platform=Platform.yandex,
        external_id="a1",
        ad_group_external_id="g1",
        campaign_external_id="c1",
        name="Объявление 1",
        desired_url="https://example.com/page",
    )
    ad_bad = AdAd(
        organization_id=org_a.id,
        connection_id=connection_yandex.id,
        platform=Platform.yandex,
        external_id="a2",
        ad_group_external_id="g1",
        campaign_external_id="c1",
        name="Объявление 2",
        desired_url="ftp://example.com",
    )
    db.add_all([camp, group, ad_ok, ad_bad])
    db.commit()

    resp = client.post(f"/api/connections/{connection_yandex.id}/utm/reconcile", headers=auth_headers)
    assert resp.status_code == 200

    db.refresh(ad_ok)
    db.refresh(ad_bad)
    assert ad_ok.final_url
    assert ad_ok.url_status == "ok"
    assert ad_ok.utm_hash
    assert ad_bad.final_url is None
    assert ad_bad.url_status == "blocked_scheme"

    status = client.get(f"/api/connections/{connection_yandex.id}/utm/status", headers=auth_headers)
    assert status.status_code == 200
    body = status.json()
    assert body["ok"] == 1
    assert body["blocked_scheme"] == 1

    token_b = create_access_token(str(user_b.id))["access_token"]
    resp_forbidden = client.post(
        f"/api/connections/{connection_yandex.id}/utm/reconcile",
        headers={"Authorization": f"Bearer {token_b}", "X-Org-Id": str(user_b.active_organization_id)},
    )
    assert resp_forbidden.status_code == 404
