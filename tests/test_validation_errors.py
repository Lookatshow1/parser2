from fastapi.testclient import TestClient


def test_connection_validation_error_for_missing_credentials(client: TestClient, auth_context):
    response = client.post(
        "/api/connections",
        json={"platform": "vk", "credentials_json": {}},
        headers=auth_context["headers"],
    )
    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "validation_error"
    assert payload["error"]["message"] == "Validation failed"
    details_text = str(payload["error"]["details"])
    assert "access_token" in details_text or "version" in details_text
