def test_utm_rules_crud(client, auth_headers):
    resp = client.get("/api/settings/utm/rules", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []

    create = client.post(
        "/api/settings/utm/rules",
        headers=auth_headers,
        json={
            "match_campaign_contains": "бренд",
            "template_json": {"utm_campaign_tpl": "brand_{campaign_id}"},
        },
    )
    assert create.status_code == 200
    rule = create.json()
    assert rule["match_campaign_contains"] == "бренд"

    update = client.patch(
        f"/api/settings/utm/rules/{rule['id']}",
        headers=auth_headers,
        json={"is_enabled": False},
    )
    assert update.status_code == 200
    assert update.json()["is_enabled"] is False
