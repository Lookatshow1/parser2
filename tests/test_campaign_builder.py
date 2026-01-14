from app.db.models import CampaignStatus


def _create_campaign(client, org_id, headers):
    payload = {
        "platform": "yandex",
        "name": "Test Campaign",
        "objective": "Рост заявок",
        "status": "draft",
        "budget_total": 10000,
        "budget_daily": 500,
    }
    resp = client.post(f"/api/orgs/{org_id}/campaigns", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_group(client, campaign_id, headers):
    payload = {
        "campaign_id": campaign_id,
        "name": "Group A",
        "status": "draft",
        "targeting_json": {},
    }
    resp = client.post("/api/ad-groups", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_ad(client, group_id, headers):
    payload = {
        "ad_group_id": group_id,
        "name": "Ad 1",
        "status": "draft",
        "creative_json": {"title": "Hello", "text": "World"},
    }
    resp = client.post("/api/ads", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_campaign_tree_endpoint(client, auth_context):
    org_id = auth_context["org"].id
    headers = auth_context["headers"]

    campaign = _create_campaign(client, org_id, headers)
    group = _create_group(client, campaign["id"], headers)
    _create_ad(client, group["id"], headers)

    resp = client.get(f"/api/orgs/{org_id}/campaigns/{campaign['id']}/tree", headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["campaign"]["id"] == campaign["id"]
    assert len(data["campaign"]["ad_groups"]) == 1
    assert len(data["campaign"]["ad_groups"][0]["ads"]) == 1


def test_publish_campaign_cascades_status(client, auth_context):
    org_id = auth_context["org"].id
    headers = auth_context["headers"]

    campaign = _create_campaign(client, org_id, headers)
    group = _create_group(client, campaign["id"], headers)
    ad = _create_ad(client, group["id"], headers)

    resp = client.post(f"/api/orgs/{org_id}/campaigns/{campaign['id']}/publish", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == CampaignStatus.active.value

    group_resp = client.get(f"/api/ad-groups/{group['id']}", headers=headers)
    assert group_resp.status_code == 200, group_resp.text
    assert group_resp.json()["status"] == CampaignStatus.active.value

    ad_resp = client.get(f"/api/ads/{ad['id']}", headers=headers)
    assert ad_resp.status_code == 200, ad_resp.text
    assert ad_resp.json()["status"] == CampaignStatus.active.value
