from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.models import Advertiser


def test_connection_does_not_leak_credentials(client: TestClient, db: Session, auth_context):
    advertiser = Advertiser(name="Cred Advertiser")
    db.add(advertiser)
    db.commit()
    db.refresh(advertiser)

    payload = {
        "platform": "stub",
        "credentials_json": {"token": "secret"},
        "advertiser_id": advertiser.id,
    }
    create_resp = client.post("/api/connections", json=payload, headers=auth_context["headers"])
    assert create_resp.status_code == 200
    assert "credentials_json" not in create_resp.json()
    assert create_resp.json().get("credentials_present") is True

    list_resp = client.get("/api/connections", headers=auth_context["headers"])
    assert list_resp.status_code == 200
    for item in list_resp.json()["items"]:
        assert "credentials_json" not in item


def test_connection_validation_errors_by_platform(client: TestClient, auth_context):
    bad_vk = client.post(
        "/api/connections",
        json={"platform": "vk", "credentials_json": {}},
        headers=auth_context["headers"],
    )
    assert bad_vk.status_code == 422

    bad_ozon = client.post(
        "/api/connections",
        json={"platform": "ozon", "credentials_json": {"client_id": "x"}},
        headers=auth_context["headers"],
    )
    assert bad_ozon.status_code == 422

    bad_yandex = client.post(
        "/api/connections",
        json={"platform": "yandex", "credentials_json": {}},
        headers=auth_context["headers"],
    )
    assert bad_yandex.status_code == 422
