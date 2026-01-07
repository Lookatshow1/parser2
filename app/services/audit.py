from __future__ import annotations

from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.db.models import OrgAuditEvent

_REDACT_KEYS = {"token", "invite_token", "raw_token", "password", "credentials", "credentials_json"}


def _sanitize_meta(meta: dict[str, Any] | None) -> dict[str, Any]:
    if not meta:
        return {}
    return {key: value for key, value in meta.items() if key not in _REDACT_KEYS}


def log_org_event(
    db: Session,
    organization_id: int,
    actor_user_id: int | None,
    action: str,
    subject_type: str | None = None,
    subject_id: int | None = None,
    meta: dict[str, Any] | None = None,
    request: Request | None = None,
) -> None:
    ip = None
    user_agent = None
    if request is not None:
        ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
    event = OrgAuditEvent(
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        action=action,
        subject_type=subject_type,
        subject_id=subject_id,
        meta=_sanitize_meta(meta),
        ip=ip,
        user_agent=user_agent,
    )
    db.add(event)
    db.commit()
