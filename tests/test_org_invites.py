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
        "/api/invites/accept",
        json={"token": invite_token},
        headers={"Authorization": f"Bearer {token_invitee}"},
    )
    assert accept_resp.status_code == 200
    assert accept_resp.json()["organization_id"] == org_id

    orgs = client.get("/api/orgs", headers={"Authorization": f"Bearer {token_invitee}"})
    assert orgs.status_code == 200
    assert any(item["id"] == org_id for item in orgs.json()["items"])

    members = client.get(f"/api/orgs/{org_id}/members", headers={"Authorization": f"Bearer {token_invitee}"})
    assert members.status_code == 200
    assert any(member["email"] == "invitee@example.com" for member in members.json())

    audit = client.get(
        f"/api/orgs/{org_id}/audit",
        headers={"Authorization": f"Bearer {token_owner}"},
    )
    assert audit.status_code == 200
    actions = [item["action"] for item in audit.json()["items"]]
    assert "invite_created" in actions
    assert "invite_accepted" in actions


def test_invite_preview_active(client: TestClient):
    token_owner = _register_and_login(client, "owner_preview@example.com")
    org_id = _create_org(client, token_owner, "Preview Org")

    invite_resp = client.post(
        f"/api/orgs/{org_id}/invites",
        json={"email": "preview@example.com", "role": "member"},
        headers={"Authorization": f"Bearer {token_owner}"},
    )
    assert invite_resp.status_code == 201
    invite_token = invite_resp.json()["invite_token"]

    preview = client.get(f"/api/invites/{invite_token}/preview")
    assert preview.status_code == 200
    body = preview.json()
    assert body["status"] == "active"
    assert body["organization_id"] == org_id
    assert body["invited_email"] == "preview@example.com"


def test_invite_send_tracking_and_resend(client: TestClient):
    token_owner = _register_and_login(client, "owner_send@example.com")
    org_id = _create_org(client, token_owner, "Send Org")

    invite_resp = client.post(
        f"/api/orgs/{org_id}/invites",
        json={"email": "send_user@example.com", "role": "member"},
        headers={"Authorization": f"Bearer {token_owner}"},
    )
    assert invite_resp.status_code == 201
    invite_body = invite_resp.json()
    invite_id = invite_body["id"]
    assert invite_body["send_count"] == 1
    assert invite_body["sent_at"] is not None
    assert invite_body["last_error"] in {None, ""}

    resend = client.post(
        f"/api/orgs/{org_id}/invites/{invite_id}/resend",
        json={},
        headers={"Authorization": f"Bearer {token_owner}"},
    )
    assert resend.status_code == 200
    resend_body = resend.json()
    assert resend_body["send_count"] == 2

def test_signup_with_invite_token(client: TestClient):
    token_owner = _register_and_login(client, "owner_signup@example.com")
    org_id = _create_org(client, token_owner, "Signup Org")

    invite_resp = client.post(
        f"/api/orgs/{org_id}/invites",
        json={"email": "signup_user@example.com", "role": "member"},
        headers={"Authorization": f"Bearer {token_owner}"},
    )
    assert invite_resp.status_code == 201
    invite_token = invite_resp.json()["invite_token"]

    signup_resp = client.post(
        "/api/auth/register",
        json={"email": "signup_user@example.com", "password": "secret123", "invite_token": invite_token},
    )
    assert signup_resp.status_code == 201

    login = client.post("/api/auth/login", json={"email": "signup_user@example.com", "password": "secret123"})
    assert login.status_code == 200
    token_user = login.json()["access_token"]

    members = client.get(
        f"/api/orgs/{org_id}/members",
        headers={"Authorization": f"Bearer {token_user}"},
    )
    assert members.status_code == 200
    assert any(member["email"] == "signup_user@example.com" for member in members.json())

    audit = client.get(
        f"/api/orgs/{org_id}/audit",
        headers={"Authorization": f"Bearer {token_owner}"},
    )
    assert audit.status_code == 200
    actions = [item["action"] for item in audit.json()["items"]]
    assert "invite_accepted" in actions


def test_signup_invite_email_mismatch(client: TestClient):
    token_owner = _register_and_login(client, "owner_mismatch_signup@example.com")
    org_id = _create_org(client, token_owner, "Mismatch Signup Org")

    invite_resp = client.post(
        f"/api/orgs/{org_id}/invites",
        json={"email": "expected_signup@example.com", "role": "member"},
        headers={"Authorization": f"Bearer {token_owner}"},
    )
    assert invite_resp.status_code == 201
    invite_token = invite_resp.json()["invite_token"]

    signup_resp = client.post(
        "/api/auth/register",
        json={"email": "other_signup@example.com", "password": "secret123", "invite_token": invite_token},
    )
    assert signup_resp.status_code == 400
    assert signup_resp.json()["error"]["message"] == "invite_email_mismatch"


def test_invite_email_mismatch_rejected(client: TestClient):
    token_owner = _register_and_login(client, "owner_mismatch@example.com")
    org_id = _create_org(client, token_owner, "Mismatch Org")

    invite_resp = client.post(
        f"/api/orgs/{org_id}/invites",
        json={"email": "expected@example.com", "role": "member"},
        headers={"Authorization": f"Bearer {token_owner}"},
    )
    assert invite_resp.status_code == 201
    invite_token = invite_resp.json()["invite_token"]

    token_other = _register_and_login(client, "other@example.com")
    accept_resp = client.post(
        "/api/invites/accept",
        json={"token": invite_token},
        headers={"Authorization": f"Bearer {token_other}"},
    )
    assert accept_resp.status_code == 403


def test_rbac_viewer_cannot_write(client: TestClient):
    token_owner = _register_and_login(client, "owner_viewer@example.com")
    org_id = _create_org(client, token_owner, "Viewer Org")

    invite_resp = client.post(
        f"/api/orgs/{org_id}/invites",
        json={"email": "viewer@example.com", "role": "member"},
        headers={"Authorization": f"Bearer {token_owner}"},
    )
    assert invite_resp.status_code == 201
    invite_token = invite_resp.json()["invite_token"]

    token_viewer = _register_and_login(client, "viewer@example.com")
    accept_resp = client.post(
        "/api/invites/accept",
        json={"token": invite_token},
        headers={"Authorization": f"Bearer {token_viewer}"},
    )
    assert accept_resp.status_code == 200

    members_resp = client.get(
        f"/api/orgs/{org_id}/members",
        headers={"Authorization": f"Bearer {token_owner}"},
    )
    assert members_resp.status_code == 200
    viewer_member = next(
        (member for member in members_resp.json() if member["email"] == "viewer@example.com"),
        None,
    )
    assert viewer_member is not None

    role_update = client.patch(
        f"/api/orgs/{org_id}/members/{viewer_member['user_id']}",
        json={"role": "viewer"},
        headers={"Authorization": f"Bearer {token_owner}"},
    )
    assert role_update.status_code == 200

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
        json={"email": "member_invite@example.com", "role": "member"},
        headers={"Authorization": f"Bearer {token_owner}"},
    )
    assert invite_resp.status_code == 201
    invite_token = invite_resp.json()["invite_token"]

    token_viewer = _register_and_login(client, "member_invite@example.com")
    accept_resp = client.post(
        "/api/invites/accept",
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


def test_revoke_invite_blocks_accept(client: TestClient):
    token_owner = _register_and_login(client, "owner_revoke@example.com")
    org_id = _create_org(client, token_owner, "Revoke Org")

    invite_resp = client.post(
        f"/api/orgs/{org_id}/invites",
        json={"email": "revoked@example.com", "role": "member"},
        headers={"Authorization": f"Bearer {token_owner}"},
    )
    assert invite_resp.status_code == 201
    invite_token = invite_resp.json()["invite_token"]
    invite_id = invite_resp.json()["id"]

    revoke = client.post(
        f"/api/orgs/{org_id}/invites/{invite_id}/revoke",
        headers={"Authorization": f"Bearer {token_owner}"},
    )
    assert revoke.status_code == 200

    token_invitee = _register_and_login(client, "revoked@example.com")
    accept_resp = client.post(
        "/api/invites/accept",
        json={"token": invite_token},
        headers={"Authorization": f"Bearer {token_invitee}"},
    )
    assert accept_resp.status_code == 409

    audit = client.get(
        f"/api/orgs/{org_id}/audit",
        headers={"Authorization": f"Bearer {token_owner}"},
    )
    assert audit.status_code == 200
    actions = [item["action"] for item in audit.json()["items"]]
    assert "invite_revoked" in actions


def test_last_owner_cannot_leave(client: TestClient):
    token_owner = _register_and_login(client, "owner_leave@example.com")
    org_id = _create_org(client, token_owner, "Leave Org")

    leave_resp = client.post(
        f"/api/orgs/{org_id}/leave",
        headers={"Authorization": f"Bearer {token_owner}"},
    )
    assert leave_resp.status_code == 409


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
