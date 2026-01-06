from fastapi.testclient import TestClient


def test_connection_validation_error_for_missing_credentials(client: TestClient):
    response = client.post(
        "/api/connections",
        json={"platform": "yandex", "credentials_json": {}},
    )
    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "validation_error"
    assert payload["error"]["message"] == "Validation failed"
    details_text = str(payload["error"]["details"])
    assert "token" in details_text
