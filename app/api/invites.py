from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.schemas import InvitePreviewResponse, OrgInviteAcceptRequest, OrgInviteAcceptResponse
from app.api.orgs import _accept_invite, _hash_token
from app.db.models import Organization
from app.services.invite_service import get_invite_by_token, resolve_invite_status
from app.db.models import User
from app.db.session import get_db

router = APIRouter(prefix="/invites", tags=["orgs"])


@router.get("/{token}/preview", response_model=InvitePreviewResponse)
def preview_invite(token: str, db: Session = Depends(get_db)):
    token_hash = _hash_token(token)
    invite = get_invite_by_token(db, token_hash)
    status = resolve_invite_status(invite)
    if status == "not_found":
        return JSONResponse(
            status_code=404,
            content=InvitePreviewResponse(status="not_found").model_dump(),
        )
    org = db.query(Organization).get(invite.organization_id) if invite else None
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return InvitePreviewResponse(
        organization_id=org.id,
        organization_name=org.name,
        invited_email=invite.invited_email,
        role=invite.role,
        expires_at=invite.expires_at,
        status=status,
    )


@router.post("/accept", response_model=OrgInviteAcceptResponse)
def accept_invite(
    payload: OrgInviteAcceptRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _accept_invite(payload, user, db, request)
