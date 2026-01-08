from fastapi.testclient import TestClient


def test_register_login_and_me(client: TestClient):
    resp = client.post("/api/auth/register", json={"email": "auth@example.com", "password": "secret123"})
    assert resp.status_code == 201

    login = client.post("/api/auth/login", json={"email": "auth@example.com", "password": "secret123"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    refresh_token = login.json()["refresh_token"]

    bad_login = client.post("/api/auth/login", json={"email": "auth@example.com", "password": "wrong"})
    assert bad_login.status_code == 401

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "auth@example.com"

    refreshed = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert refreshed.status_code == 200
    assert "access_token" in refreshed.json()


def test_org_membership_and_isolation(client: TestClient):
    client.post("/api/auth/register", json={"email": "orgs@example.com", "password": "secret123"})
    login = client.post("/api/auth/login", json={"email": "orgs@example.com", "password": "secret123"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    default_org_list = client.get("/api/connections", headers=headers)
    assert default_org_list.status_code == 200

    org_a = client.post("/api/orgs", json={"name": "Org A"}, headers=headers)
    assert org_a.status_code == 201
    org_a_id = org_a.json()["id"]
    activate_a = client.post(f"/api/orgs/{org_a_id}/activate", headers=headers)
    assert activate_a.status_code == 200

    connection = client.post(
        "/api/connections",
        json={"platform": "stub", "credentials_json": {}},
        headers=headers,
    )
    assert connection.status_code == 200
    connection_id = connection.json()["id"]

    org_b = client.post("/api/orgs", json={"name": "Org B"}, headers=headers)
    assert org_b.status_code == 201
    org_b_id = org_b.json()["id"]
    activate_b = client.post(f"/api/orgs/{org_b_id}/activate", headers=headers)
    assert activate_b.status_code == 200

    list_b = client.get("/api/connections", headers=headers)
    assert list_b.status_code == 200
    assert list_b.json()["items"] == []

    sync_b = client.post(
        "/api/sync-runs",
        json={"connection_id": connection_id, "params_json": {"date_from": "2023-01-01", "date_to": "2023-01-03"}},
        headers=headers,
    )
    assert sync_b.status_code == 404

    snapshots_b = client.get(
        f"/api/connections/{connection_id}/snapshots",
        params={"date_from": "2023-01-01", "date_to": "2023-01-03"},
        headers=headers,
    )
    assert snapshots_b.status_code == 404
