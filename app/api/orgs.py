import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_current_user
from app.api.schemas import (
    OrgInviteAcceptRequest,
    OrgInviteAcceptResponse,
    OrgInviteCreateRequest,
    OrgInviteCreateResponse,
    OrgInviteListResponse,
    OrgInviteOut,
    OrgInviteResendRequest,
    OrgInviteResendResponse,
    OrgAuditListResponse,
    OrgMemberOut,
    OrgMemberRoleUpdateRequest,
    OrganizationCreateRequest,
    OrganizationListResponse,
    OrganizationOut,
    OrganizationSwitchRequest,
)
from app.db.models import Membership, MembershipRole, OrgInvite, Organization, User, OrgAuditEvent
from app.db.session import get_db
from app.services.rbac import can_invite, can_manage_members, can_change_roles, ROLE_OWNER
from app.core.config import get_settings
from app.services.audit import log_org_event
from app.services.email_service import send_invite_email

router = APIRouter(prefix="/orgs", tags=["orgs"])


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _normalize_email(value: str) -> str:
    return value.strip().lower()


def _is_invite_active(invite: OrgInvite, now: datetime) -> bool:
    return (
        invite.status == "pending"
        and invite.accepted_at is None
        and invite.revoked_at is None
        and invite.expires_at > now
    )


def _build_join_url(raw_token: str) -> str | None:
    settings = get_settings()
    if not settings.web_base_url:
        return None
    base = settings.web_base_url.rstrip("/")
    return f"{base}/invite?token={raw_token}"


def _send_invite_and_track(
    db: Session,
    invite: OrgInvite,
    raw_token: str,
    action_success: str,
    action_failure: str,
    request: Request | None,
    actor_user_id: int | None,
    org_name: str,
) -> None:
    join_url = _build_join_url(raw_token)
    sent, error = send_invite_email(
        to_email=invite.invited_email,
        org_name=org_name,
        role=invite.role,
        expires_at=invite.expires_at,
        join_url=join_url,
        raw_token=raw_token,
    )
    invite.send_count = (invite.send_count or 0) + 1
    if sent:
        invite.sent_at = datetime.now(timezone.utc)
        invite.last_error = None
        log_org_event(
            db,
            organization_id=invite.organization_id,
            actor_user_id=actor_user_id,
            action=action_success,
            subject_type="invite",
            subject_id=invite.id,
            meta={"email": invite.invited_email, "role": invite.role},
            request=request,
        )
    else:
        invite.last_error = error
        log_org_event(
            db,
            organization_id=invite.organization_id,
            actor_user_id=actor_user_id,
            action=action_failure,
            subject_type="invite",
            subject_id=invite.id,
            meta={"email": invite.invited_email, "role": invite.role, "error": error or "send_failed"},
            request=request,
        )
    db.commit()
    db.refresh(invite)


def _require_membership(db: Session, user_id: int, org_id: int) -> Membership:
    membership = (
        db.query(Membership)
        .filter(Membership.user_id == user_id, Membership.organization_id == org_id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Forbidden for this organization")
    return membership


@router.post("", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED)
def create_org(
    payload: OrganizationCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org = Organization(name=payload.name)
    db.add(org)
    db.commit()
    db.refresh(org)

    membership = Membership(user_id=user.id, organization_id=org.id, role=MembershipRole.owner.value)
    db.add(membership)
    user.active_organization_id = org.id
    db.commit()
    return org


@router.get("", response_model=OrganizationListResponse)
def list_orgs(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    orgs = (
        db.query(Organization)
        .join(Membership, Membership.organization_id == Organization.id)
        .filter(Membership.user_id == user.id)
        .order_by(Organization.id.asc())
        .all()
    )
    return {"items": orgs}


@router.get("/active", response_model=OrganizationOut)
def get_active_org(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user.active_organization_id:
        raise HTTPException(status_code=409, detail="Select organization")
    org = db.query(Organization).get(user.active_organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.post("/{org_id}/activate", response_model=OrganizationOut)
@router.post("/{org_id}/switch", response_model=OrganizationOut)
def activate_org(
    org_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = (
        db.query(Membership)
        .filter(Membership.user_id == user.id, Membership.organization_id == org_id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Forbidden for this organization")
    org = db.query(Organization).get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    user.active_organization_id = org.id
    db.commit()
    return org


@router.post("/switch", response_model=OrganizationOut)
def switch_org(
    payload: OrganizationSwitchRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = (
        db.query(Membership)
        .filter(Membership.user_id == user.id, Membership.organization_id == payload.organization_id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Forbidden for this organization")
    org = db.query(Organization).get(payload.organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    user.active_organization_id = org.id
    db.commit()
    return org


@router.post("/{org_id}/invites", response_model=OrgInviteCreateResponse, status_code=status.HTTP_201_CREATED)
def create_invite(
    org_id: int,
    payload: OrgInviteCreateRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org = db.query(Organization).get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    membership = _require_membership(db, user.id, org_id)
    if not can_invite(membership.role):
        raise HTTPException(status_code=403, detail="Insufficient role for inviting")

    if payload.role.value == MembershipRole.owner.value:
        raise HTTPException(status_code=400, detail="Owner role cannot be invited")
    if payload.role.value not in {MembershipRole.admin.value, MembershipRole.member.value}:
        raise HTTPException(status_code=400, detail="Invalid invite role")

    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)

    expires_in_days = payload.expires_in_days or 7
    expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

    normalized_email = _normalize_email(str(payload.email))
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        existing_membership = (
            db.query(Membership)
            .filter(Membership.organization_id == org_id, Membership.user_id == existing_user.id)
            .first()
        )
        if existing_membership:
            raise HTTPException(status_code=409, detail="User already belongs to organization")

    now = datetime.now(timezone.utc)
    active_invite = (
        db.query(OrgInvite)
        .filter(
            OrgInvite.organization_id == org_id,
            OrgInvite.invited_email == normalized_email,
            OrgInvite.status == "pending",
            OrgInvite.accepted_at.is_(None),
            OrgInvite.revoked_at.is_(None),
            OrgInvite.expires_at > now,
        )
        .first()
    )
    if active_invite:
        raise HTTPException(status_code=409, detail="Active invite already exists")

    invite = OrgInvite(
        organization_id=org_id,
        invited_email=normalized_email,
        role=payload.role.value,
        status="pending",
        token_hash=token_hash,
        expires_at=expires_at,
        created_by_user_id=user.id,
    )
    db.add(invite)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Active invite already exists") from None
    db.refresh(invite)
    log_org_event(
        db,
        organization_id=org_id,
        actor_user_id=user.id,
        action="invite_created",
        subject_type="invite",
        subject_id=invite.id,
        meta={"email": invite.invited_email, "role": invite.role},
        request=request,
    )
    _send_invite_and_track(
        db=db,
        invite=invite,
        raw_token=raw_token,
        action_success="invite_sent",
        action_failure="invite_send_failed",
        request=request,
        actor_user_id=user.id,
        org_name=org.name,
    )
    join_url = _build_join_url(raw_token)
    response = OrgInviteCreateResponse(
        **OrgInviteOut.model_validate(invite).model_dump(),
        invite_token=raw_token,
        join_url=join_url,
    )
    return response


@router.get("/{org_id}/invites", response_model=OrgInviteListResponse)
def list_invites(
    org_id: int,
    status_filter: str | None = Query(None, alias="status"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = _require_membership(db, user.id, org_id)
    if not can_invite(membership.role):
        raise HTTPException(status_code=403, detail="Insufficient role for invites")

    now = datetime.now(timezone.utc)
    pending_expired = (
        db.query(OrgInvite)
        .filter(
            OrgInvite.organization_id == org_id,
            OrgInvite.status == "pending",
            OrgInvite.expires_at <= now,
            OrgInvite.revoked_at.is_(None),
        )
        .all()
    )
    for invite in pending_expired:
        invite.status = "expired"
    if pending_expired:
        db.commit()

    query = db.query(OrgInvite).filter(OrgInvite.organization_id == org_id)
    if status_filter:
        query = query.filter(OrgInvite.status == status_filter)
    else:
        query = query.filter(
            OrgInvite.status == "pending",
            OrgInvite.revoked_at.is_(None),
            OrgInvite.expires_at > now,
        )
    items = query.order_by(OrgInvite.created_at.desc()).all()
    return {"items": items}


def _accept_invite(
    payload: OrgInviteAcceptRequest,
    user: User,
    db: Session,
    request: Request | None = None,
) -> OrgInviteAcceptResponse:
    token_hash = _hash_token(payload.token)
    invite = db.query(OrgInvite).filter(OrgInvite.token_hash == token_hash).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    now = datetime.now(timezone.utc)
    if invite.status == "revoked" or invite.revoked_at:
        raise HTTPException(status_code=409, detail="Invite revoked")
    if invite.status == "accepted" or invite.accepted_at:
        raise HTTPException(status_code=409, detail="Invite already accepted")
    if invite.expires_at <= now:
        invite.status = "expired"
        db.commit()
        raise HTTPException(status_code=409, detail="Invite expired")

    if _normalize_email(user.email) != _normalize_email(invite.invited_email):
        raise HTTPException(status_code=403, detail="Invite email does not match current user")

    membership = (
        db.query(Membership)
        .filter(Membership.organization_id == invite.organization_id, Membership.user_id == user.id)
        .first()
    )
    if not membership:
        membership = Membership(
            organization_id=invite.organization_id,
            user_id=user.id,
            role=invite.role,
        )
        db.add(membership)

    invite.accepted_at = now
    invite.accepted_by_user_id = user.id
    invite.status = "accepted"
    if not user.active_organization_id:
        user.active_organization_id = invite.organization_id
    db.commit()

    log_org_event(
        db,
        organization_id=invite.organization_id,
        actor_user_id=user.id,
        action="invite_accepted",
        subject_type="invite",
        subject_id=invite.id,
        meta={"email": invite.invited_email, "role": invite.role},
        request=request,
    )
    org = db.query(Organization).get(invite.organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return OrgInviteAcceptResponse(
        organization_id=org.id,
        organization_name=org.name,
        role=membership.role if membership else invite.role,
        active_organization_id=user.active_organization_id,
    )


@router.post("/invites/accept", response_model=OrgInviteAcceptResponse)
def accept_invite(
    payload: OrgInviteAcceptRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _accept_invite(payload, user, db, request)


@router.get("/{org_id}/members", response_model=list[OrgMemberOut])
def list_members(
    org_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_membership(db, user.id, org_id)
    members = (
        db.query(Membership, User)
        .join(User, User.id == Membership.user_id)
        .filter(Membership.organization_id == org_id)
        .order_by(Membership.id.asc())
        .all()
    )
    return [
        OrgMemberOut(
            user_id=member.user_id,
            email=user_row.email,
            role=member.role,
            joined_at=member.created_at,
            is_you=member.user_id == user.id,
        )
        for member, user_row in members
    ]


@router.patch("/{org_id}/members/{member_user_id}", response_model=OrgMemberOut)
def update_member_role(
    org_id: int,
    member_user_id: int,
    payload: OrgMemberRoleUpdateRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = _require_membership(db, user.id, org_id)
    if not can_change_roles(membership.role):
        raise HTTPException(status_code=403, detail="Only owner can change roles")

    target = (
        db.query(Membership)
        .filter(Membership.organization_id == org_id, Membership.user_id == member_user_id)
        .first()
    )
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")

    owners = (
        db.query(Membership)
        .filter(Membership.organization_id == org_id, Membership.role == ROLE_OWNER)
        .count()
    )
    if target.role == ROLE_OWNER and payload.role.value != ROLE_OWNER and owners <= 1:
        raise HTTPException(status_code=409, detail="Organization must have at least one owner")

    old_role = target.role
    target.role = payload.role.value
    db.commit()

    member_user = db.query(User).get(member_user_id)
    log_org_event(
        db,
        organization_id=org_id,
        actor_user_id=user.id,
        action="member_role_changed",
        subject_type="member",
        subject_id=target.user_id,
        meta={"old_role": old_role, "new_role": target.role, "email": member_user.email if member_user else ""},
        request=request,
    )
    return OrgMemberOut(
        user_id=target.user_id,
        email=member_user.email if member_user else "",
        role=target.role,
        joined_at=target.created_at,
        is_you=member_user_id == user.id,
    )


@router.delete("/{org_id}/members/{member_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member(
    org_id: int,
    member_user_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = _require_membership(db, user.id, org_id)
    if not can_manage_members(membership.role):
        raise HTTPException(status_code=403, detail="Insufficient role to manage members")

    target = (
        db.query(Membership)
        .filter(Membership.organization_id == org_id, Membership.user_id == member_user_id)
        .first()
    )
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")

    if target.role == ROLE_OWNER:
        owners = (
            db.query(Membership)
            .filter(Membership.organization_id == org_id, Membership.role == ROLE_OWNER)
            .count()
        )
        if owners <= 1:
            raise HTTPException(status_code=409, detail="Organization must have at least one owner")
        if membership.role != ROLE_OWNER:
            raise HTTPException(status_code=403, detail="Only owner can remove another owner")

    db.delete(target)
    db.commit()
    target_user = db.query(User).get(member_user_id)
    log_org_event(
        db,
        organization_id=org_id,
        actor_user_id=user.id,
        action="member_removed",
        subject_type="member",
        subject_id=target.user_id,
        meta={"email": target_user.email if target_user else ""},
        request=request,
    )


@router.post("/{org_id}/invites/{invite_id}/revoke", status_code=status.HTTP_200_OK)
def revoke_invite(
    org_id: int,
    invite_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = _require_membership(db, user.id, org_id)
    if not can_invite(membership.role):
        raise HTTPException(status_code=403, detail="Insufficient role for invites")

    invite = (
        db.query(OrgInvite)
        .filter(OrgInvite.id == invite_id, OrgInvite.organization_id == org_id)
        .first()
    )
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    if invite.status == "accepted" or invite.accepted_at:
        raise HTTPException(status_code=409, detail="Invite already accepted")
    if invite.status == "revoked":
        return {"ok": True}

    invite.status = "revoked"
    invite.revoked_at = datetime.now(timezone.utc)
    invite.revoked_by_user_id = user.id
    db.commit()
    log_org_event(
        db,
        organization_id=org_id,
        actor_user_id=user.id,
        action="invite_revoked",
        subject_type="invite",
        subject_id=invite.id,
        meta={"email": invite.invited_email, "role": invite.role},
        request=request,
    )
    return {"ok": True}


@router.post("/{org_id}/invites/{invite_id}/resend", response_model=OrgInviteResendResponse)
def resend_invite(
    org_id: int,
    invite_id: int,
    payload: OrgInviteResendRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org = db.query(Organization).get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    membership = _require_membership(db, user.id, org_id)
    if not can_invite(membership.role):
        raise HTTPException(status_code=403, detail="Insufficient role for invites")

    invite = (
        db.query(OrgInvite)
        .filter(OrgInvite.id == invite_id, OrgInvite.organization_id == org_id)
        .first()
    )
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    if invite.status == "accepted" or invite.accepted_at:
        raise HTTPException(status_code=409, detail="Invite already accepted")
    if invite.status == "revoked" or invite.revoked_at:
        raise HTTPException(status_code=409, detail="Invite revoked")

    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    expires_in_days = payload.expires_in_days or 7
    new_expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

    join_url = _build_join_url(raw_token)
    sent, error = send_invite_email(
        to_email=invite.invited_email,
        org_name=org.name,
        role=invite.role,
        expires_at=new_expires_at,
        join_url=join_url,
        raw_token=raw_token,
    )
    invite.send_count = (invite.send_count or 0) + 1
    if sent:
        invite.token_hash = token_hash
        invite.expires_at = new_expires_at
        invite.status = "pending"
        invite.sent_at = datetime.now(timezone.utc)
        invite.last_error = None
        log_org_event(
            db,
            organization_id=org_id,
            actor_user_id=user.id,
            action="invite_resent",
            subject_type="invite",
            subject_id=invite.id,
            meta={"email": invite.invited_email, "role": invite.role},
            request=request,
        )
    else:
        invite.last_error = error
        log_org_event(
            db,
            organization_id=org_id,
            actor_user_id=user.id,
            action="invite_send_failed",
            subject_type="invite",
            subject_id=invite.id,
            meta={"email": invite.invited_email, "role": invite.role, "error": error or "send_failed"},
            request=request,
        )
    db.commit()
    db.refresh(invite)
    return OrgInviteResendResponse(
        id=invite.id,
        sent_at=invite.sent_at,
        send_count=invite.send_count,
        last_error=invite.last_error,
    )


@router.post("/{org_id}/leave", status_code=status.HTTP_200_OK)
def leave_org(
    org_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = _require_membership(db, user.id, org_id)
    if membership.role == ROLE_OWNER:
        owners = (
            db.query(Membership)
            .filter(Membership.organization_id == org_id, Membership.role == ROLE_OWNER)
            .count()
        )
        if owners <= 1:
            raise HTTPException(status_code=409, detail="Organization must have at least one owner")

    db.delete(membership)
    db.commit()
    log_org_event(
        db,
        organization_id=org_id,
        actor_user_id=user.id,
        action="member_left",
        subject_type="member",
        subject_id=user.id,
        meta={"email": user.email},
        request=request,
    )

    if user.active_organization_id == org_id:
        next_membership = (
            db.query(Membership)
            .filter(Membership.user_id == user.id)
            .order_by(Membership.id.asc())
            .first()
        )
        user.active_organization_id = next_membership.organization_id if next_membership else None
        db.commit()
    return {"active_organization_id": user.active_organization_id}


@router.get("/{org_id}/audit", response_model=OrgAuditListResponse)
def list_audit_events(
    org_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_membership(db, user.id, org_id)
    query = db.query(OrgAuditEvent).filter(OrgAuditEvent.organization_id == org_id)
    total = query.count()
    items = (
        query.order_by(OrgAuditEvent.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return {"items": items, "total": total}
