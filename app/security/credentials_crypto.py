from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class CredentialsCryptoError(RuntimeError):
    pass


def is_encrypted(value: Any) -> bool:
    return isinstance(value, dict) and value.get("__enc__") is True and "ct" in value and "kid" in value


def _parse_keyring(raw: str) -> dict[str, Fernet]:
    keyring: dict[str, Fernet] = {}
    items = [item.strip() for item in raw.split(",") if item.strip()]
    for item in items:
        if ":" not in item:
            raise CredentialsCryptoError("Invalid credentials key format")
        kid, key = item.split(":", 1)
        if not kid or not key:
            raise CredentialsCryptoError("Invalid credentials key entry")
        try:
            keyring[kid] = Fernet(key)
        except Exception as exc:
            raise CredentialsCryptoError("Invalid credentials encryption key") from exc
    return keyring


@lru_cache(maxsize=1)
def _get_keyring() -> tuple[dict[str, Fernet], str | None]:
    settings = get_settings()
    raw = (settings.credentials_enc_keys or "").strip()
    if not raw:
        if settings.env == "prod":
            raise CredentialsCryptoError("CREDENTIALS_ENC_KEYS is required in prod")
        logger.warning("Credentials encryption keys are not configured; using plaintext storage.")
        return {}, None
    keyring = _parse_keyring(raw)
    if not keyring:
        raise CredentialsCryptoError("No valid credentials encryption keys configured")
    active_kid = settings.credentials_enc_active_kid or next(iter(keyring.keys()))
    if active_kid not in keyring:
        raise CredentialsCryptoError("CREDENTIALS_ENC_ACTIVE_KID is not present in CREDENTIALS_ENC_KEYS")
    return keyring, active_kid


def encryption_enabled() -> bool:
    keyring, _ = _get_keyring()
    return bool(keyring)


def encrypt_credentials(value: Any, *, kid: str | None = None) -> dict[str, Any]:
    keyring, active_kid = _get_keyring()
    if not keyring:
        return value if isinstance(value, dict) else {}
    target_kid = kid or active_kid
    if not target_kid or target_kid not in keyring:
        raise CredentialsCryptoError("Active credentials encryption key is not configured")
    payload = json.dumps(value or {}, separators=(",", ":"), sort_keys=True).encode("utf-8")
    token = keyring[target_kid].encrypt(payload).decode("utf-8")
    return {"__enc__": True, "v": 1, "kid": target_kid, "ct": token}


def decrypt_credentials(wrapper: dict[str, Any]) -> dict[str, Any]:
    if not is_encrypted(wrapper):
        raise CredentialsCryptoError("Credentials wrapper is invalid")
    keyring, _ = _get_keyring()
    if not keyring:
        raise CredentialsCryptoError("Credentials encryption keys are not configured")
    kid = wrapper.get("kid")
    fernet = keyring.get(kid)
    if not fernet:
        raise CredentialsCryptoError("Credentials encryption key not available")
    token = wrapper.get("ct")
    try:
        plaintext = fernet.decrypt(token.encode("utf-8"))
    except (InvalidToken, AttributeError) as exc:
        raise CredentialsCryptoError("Credentials decryption failed") from exc
    try:
        return json.loads(plaintext.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise CredentialsCryptoError("Credentials payload is invalid") from exc


def maybe_decrypt(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if is_encrypted(value):
        return decrypt_credentials(value)
    if isinstance(value, dict):
        return value
    raise CredentialsCryptoError("Credentials payload must be a dict")


def maybe_encrypt(value: Any) -> dict[str, Any]:
    if value is None:
        value = {}
    if is_encrypted(value):
        return value
    if not isinstance(value, dict):
        raise CredentialsCryptoError("Credentials payload must be a dict")
    return encrypt_credentials(value)


def rotate_wrapper(wrapper: dict[str, Any]) -> dict[str, Any]:
    if not is_encrypted(wrapper):
        return maybe_encrypt(wrapper)
    keyring, active_kid = _get_keyring()
    if not keyring or not active_kid:
        raise CredentialsCryptoError("Credentials encryption keys are not configured")
    if wrapper.get("kid") == active_kid:
        return wrapper
    plaintext = decrypt_credentials(wrapper)
    return encrypt_credentials(plaintext, kid=active_kid)
