from datetime import datetime, timedelta, timezone
import hashlib
import secrets
import uuid

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(subject: str) -> dict:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.access_token_algorithm)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=[settings.access_token_algorithm])


def hash_refresh_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_refresh_token_data() -> dict:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_refresh_token(raw_token)
    jti = uuid.uuid4().hex
    expires_at = now + timedelta(days=settings.refresh_token_ttl_days)
    return {
        "raw_token": raw_token,
        "token_hash": token_hash,
        "jti": jti,
        "expires_at": expires_at,
        "expires_in": settings.refresh_token_ttl_days * 86400,
    }
