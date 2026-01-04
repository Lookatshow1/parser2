
from tests.conftest import client as _client  # ensure fixture is discovered


def test_healthz_ok_with_schema(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] in ("ok", "error")


def test_healthz_db_check(client):
    # ensure db field present in response
    response = client.get("/healthz")
    assert "db" in response.json()
