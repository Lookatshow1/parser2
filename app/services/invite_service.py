from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from sqlalchemy.orm import Session

from app.db.models import OrgInvite

InviteStatus = Literal["active", "revoked", "expired", "accepted", "not_found"]


def resolve_invite_status(invite: OrgInvite | None) -> InviteStatus:
    if invite is None:
        return "not_found"
    now = datetime.now(timezone.utc)
    if invite.status == "revoked" or invite.revoked_at:
        return "revoked"
    if invite.status == "accepted" or invite.accepted_at:
        return "accepted"
    if invite.expires_at <= now or invite.status == "expired":
        return "expired"
    return "active"


def get_invite_by_token(db: Session, token_hash: str) -> OrgInvite | None:
    return db.query(OrgInvite).filter(OrgInvite.token_hash == token_hash).first()
