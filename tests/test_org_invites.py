from fastapi.testclient import TestClient


def _register_and_login(client: TestClient, email: str) -> str:
    resp = client.post("/api/auth/register", json={"email": email, "password": "secret123"})
    assert resp.status_code in {201, 409}
    login = client.post("/api/auth/login", json={"email": email, "password": "secret123"})
    assert login.status_code == 200
    return login.json()["access_token"]


def _create_org(client: TestClient, token: str, name: str) -> int:
    resp = client.post(
        "/api/orgs",
        json={"name": name},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def test_org_invite_accept_flow(client: TestClient):
    token_owner = _register_and_login(client, "owner_invite@example.com")
    org_id = _create_org(client, token_owner, "Invite Org")

    invite_resp = client.post(
        f"/api/orgs/{org_id}/invites",
        json={"email": "invitee@example.com", "role": "member"},
        headers={"Authorization": f"Bearer {token_owner}"},
    )
    assert invite_resp.status_code == 201
    invite_token = invite_resp.json()["invite_token"]

    token_invitee = _register_and_login(client, "invitee@example.com")
    accept_resp = client.post(
        "/api/orgs/invites/accept",
        json={"token": invite_token},
        headers={"Authorization": f"Bearer {token_invitee}"},
    )
    assert accept_resp.status_code == 200
    assert accept_resp.json()["id"] == org_id

    orgs = client.get("/api/orgs", headers={"Authorization": f"Bearer {token_invitee}"})
    assert orgs.status_code == 200
    assert any(item["id"] == org_id for item in orgs.json()["items"])

    members = client.get(
        f"/api/orgs/{org_id}/members",
        headers={"Authorization": f"Bearer {token_invitee}"},
    )
    assert members.status_code == 200
    assert any(member["email"] == "invitee@example.com" for member in members.json())


def test_invite_flow_new_user(client: TestClient):
    token_owner = _register_and_login(client, "owner_new_user@example.com")
    org_id = _create_org(client, token_owner, "New User Org")

    invite_resp = client.post(
        f"/api/orgs/{org_id}/invites",
        json={"email": "new_user@example.com", "role": "member"},
        headers={"Authorization": f"Bearer {token_owner}"},
    )
    assert invite_resp.status_code == 201
    invite_token = invite_resp.json()["invite_token"]

    accept_resp = client.post(
        "/api/orgs/invites/accept",
        json={"token": invite_token, "password": "secret123"},
    )
    assert accept_resp.status_code == 200
    assert accept_resp.json()["id"] == org_id

    login = client.post("/api/auth/login", json={"email": "new_user@example.com", "password": "secret123"})
    assert login.status_code == 200


def test_rbac_viewer_cannot_write(client: TestClient):
    token_owner = _register_and_login(client, "owner_viewer@example.com")
    org_id = _create_org(client, token_owner, "Viewer Org")

    invite_resp = client.post(
        f"/api/orgs/{org_id}/invites",
        json={"email": "viewer@example.com", "role": "viewer"},
        headers={"Authorization": f"Bearer {token_owner}"},
    )
    assert invite_resp.status_code == 201
    invite_token = invite_resp.json()["invite_token"]

    token_viewer = _register_and_login(client, "viewer@example.com")
    accept_resp = client.post(
        "/api/orgs/invites/accept",
        json={"token": invite_token},
        headers={"Authorization": f"Bearer {token_viewer}"},
    )
    assert accept_resp.status_code == 200

    headers = {
        "Authorization": f"Bearer {token_viewer}",
        "X-Org-Id": str(org_id),
    }
    create_conn = client.post(
        "/api/connections",
        json={"platform": "stub", "credentials_json": {}},
        headers=headers,
    )
    assert create_conn.status_code == 403

    create_sync = client.post(
        "/api/sync-runs",
        json={"connection_id": 1, "params_json": {"date_from": "2023-01-01", "date_to": "2023-01-03"}},
        headers=headers,
    )
    assert create_sync.status_code == 403


def test_rbac_invites_only_admin(client: TestClient):
    token_owner = _register_and_login(client, "owner_invite_only@example.com")
    org_id = _create_org(client, token_owner, "Invite RBAC Org")

    invite_resp = client.post(
        f"/api/orgs/{org_id}/invites",
        json={"email": "viewer_invite@example.com", "role": "viewer"},
        headers={"Authorization": f"Bearer {token_owner}"},
    )
    assert invite_resp.status_code == 201
    invite_token = invite_resp.json()["invite_token"]

    token_viewer = _register_and_login(client, "viewer_invite@example.com")
    accept_resp = client.post(
        "/api/orgs/invites/accept",
        json={"token": invite_token},
        headers={"Authorization": f"Bearer {token_viewer}"},
    )
    assert accept_resp.status_code == 200

    forbidden = client.post(
        f"/api/orgs/{org_id}/invites",
        json={"email": "another@example.com", "role": "member"},
        headers={"Authorization": f"Bearer {token_viewer}"},
    )
    assert forbidden.status_code == 403


def test_cross_org_access_hidden(client: TestClient):
    token = _register_and_login(client, "cross_org@example.com")
    org_a = _create_org(client, token, "Org A")
    headers_a = {"Authorization": f"Bearer {token}", "X-Org-Id": str(org_a)}

    connection = client.post(
        "/api/connections",
        json={"platform": "stub", "credentials_json": {}},
        headers=headers_a,
    )
    assert connection.status_code == 200
    connection_id = connection.json()["id"]

    org_b = _create_org(client, token, "Org B")
    headers_b = {"Authorization": f"Bearer {token}", "X-Org-Id": str(org_b)}

    conn_b = client.get(f"/api/connections/{connection_id}", headers=headers_b)
    assert conn_b.status_code == 404
