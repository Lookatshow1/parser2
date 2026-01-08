import base64
import importlib.util
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Connection, Organization, Platform
from app.security import credentials_crypto as cc


def _reset_crypto_cache() -> None:
    get_settings.cache_clear()
    cc._get_keyring.cache_clear()


def test_connection_credentials_encrypted_at_rest(client: TestClient, db: Session, auth_context):
    resp = client.post(
        "/api/connections",
        json={"platform": "yandex", "credentials_json": {"token": "secret"}},
        headers=auth_context["headers"],
    )
    assert resp.status_code == 200
    connection_id = resp.json()["id"]
    conn = db.query(Connection).get(connection_id)
    assert cc.is_encrypted(conn.credentials_json)


def test_encrypt_decrypt_roundtrip():
    payload = {"token": "secret", "login": "demo"}
    wrapper = cc.encrypt_credentials(payload)
    assert cc.is_encrypted(wrapper)
    decrypted = cc.maybe_decrypt(wrapper)
    assert decrypted == payload


def test_rotate_wrapper(monkeypatch):
    key_a = base64.urlsafe_b64encode(b"0" * 32).decode()
    key_b = base64.urlsafe_b64encode(b"1" * 32).decode()
    monkeypatch.setenv("CREDENTIALS_ENC_KEYS", f"a:{key_a},b:{key_b}")
    monkeypatch.setenv("CREDENTIALS_ENC_ACTIVE_KID", "a")
    _reset_crypto_cache()

    wrapper = cc.encrypt_credentials({"token": "secret"})
    assert wrapper["kid"] == "a"

    monkeypatch.setenv("CREDENTIALS_ENC_ACTIVE_KID", "b")
    _reset_crypto_cache()
    rotated = cc.rotate_wrapper(wrapper)
    assert rotated["kid"] == "b"
    assert cc.maybe_decrypt(rotated)["token"] == "secret"


def test_invalid_wrapper_error(monkeypatch):
    monkeypatch.setenv("CREDENTIALS_ENC_KEYS", "k1:MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=")
    monkeypatch.setenv("CREDENTIALS_ENC_ACTIVE_KID", "k1")
    _reset_crypto_cache()
    with pytest.raises(cc.CredentialsCryptoError):
        cc.decrypt_credentials({"__enc__": True, "kid": "missing", "ct": "bad"})


def test_migration_encrypts_plaintext(db: Session):
    org = Organization(name="Migration Org")
    db.add(org)
    db.commit()
    db.refresh(org)
    conn = Connection(
        organization_id=org.id,
        advertiser_id=None,
        platform=Platform.yandex,
        name="Legacy",
        credentials_json={"token": "legacy"},
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    assert not cc.is_encrypted(conn.credentials_json)

    migration_path = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "0016_encrypt_existing_credentials.py"
    spec = importlib.util.spec_from_file_location("encrypt_migration", migration_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.encrypt_existing_credentials(db.get_bind())
    db.refresh(conn)
    assert cc.is_encrypted(conn.credentials_json)
