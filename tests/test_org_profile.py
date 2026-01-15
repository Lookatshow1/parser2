from app.services.auth_service import create_access_token


def test_org_profile_get_update(client, auth_headers):
    response = client.get("/api/settings/org-profile", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["organization_id"]
    assert data["timezone"] == "Europe/Moscow"
    assert data["currency"] == "RUB"

    payload = {
        "legal_type": "ООО",
        "legal_name": "Тестовая организация",
        "inn": "7700000000",
        "email_for_docs": "docs@example.com",
    }
    response = client.put("/api/settings/org-profile", headers=auth_headers, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["legal_name"] == "Тестовая организация"
    assert data["inn"] == "7700000000"
    assert data["email_for_docs"] == "docs@example.com"


def test_org_profile_scoping(client, auth_headers, user_b, org_b):
    response = client.get("/api/settings/org-profile", headers=auth_headers)
    assert response.status_code == 200
    org_a_id = response.json()["organization_id"]

    token = create_access_token(str(user_b.id))["access_token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Org-Id": str(org_b.id),
    }
    response = client.get("/api/settings/org-profile", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["organization_id"] == org_b.id
    assert data["organization_id"] != org_a_id
