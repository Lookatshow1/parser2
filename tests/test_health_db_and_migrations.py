from fastapi.testclient import TestClient

def test_health_check(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "db" in data
    assert "migrations" in data

    # Since we run migrations before tests, both should be ok
    assert data["db"]["ok"] is True
    assert data["migrations"]["ok"] is True
    assert data["status"] == "ok"

    assert data["migrations"]["current"] is not None
    assert data["migrations"]["head"] is not None
    assert data["migrations"]["current"] == data["migrations"]["head"]
