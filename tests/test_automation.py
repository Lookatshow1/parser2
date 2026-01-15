from app.db.models import OrgAutomationAction


def test_automation_run_creates_actions(client, db, auth_headers, org_a, connection_yandex):
    resp = client.post("/api/automation/run", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] in ("running", "success")

    actions = db.query(OrgAutomationAction).filter(OrgAutomationAction.organization_id == org_a.id).all()
    assert len(actions) > 0


def test_automation_actions_scoped(client, auth_headers, org_b, user_b):
    from app.services.auth_service import create_access_token

    token_b = create_access_token(str(user_b.id))["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}", "X-Org-Id": str(org_b.id)}
    resp = client.get("/api/automation/actions", headers=headers_b)
    assert resp.status_code == 200
