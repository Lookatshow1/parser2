import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_current_user, get_optional_user
from app.api.schemas import (
    OrgInviteAcceptRequest,
    OrgInviteCreateRequest,
    OrgInviteCreateResponse,
    OrgInviteListResponse,
    OrgInviteOut,
    OrgMemberOut,
    OrgMemberRoleUpdateRequest,
    OrganizationCreateRequest,
    OrganizationListResponse,
    OrganizationOut,
    OrganizationSwitchRequest,
)
from app.db.models import Membership, MembershipRole, OrgInvite, Organization, User
from app.db.session import get_db
from app.services.rbac import can_invite, can_manage_members, ROLE_OWNER
from app.services.auth_service import get_password_hash

router = APIRouter(prefix="/orgs", tags=["orgs"])


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


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
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = _require_membership(db, user.id, org_id)
    if not can_invite(membership.role):
        raise HTTPException(status_code=403, detail="Insufficient role for inviting")

    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)

    expires_in_days = payload.expires_in_days or 7
    expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

    normalized_email = str(payload.email).strip().lower()
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        existing_membership = (
            db.query(Membership)
            .filter(Membership.organization_id == org_id, Membership.user_id == existing_user.id)
            .first()
        )
        if existing_membership:
            raise HTTPException(status_code=409, detail="User already belongs to organization")

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
    return OrgInviteCreateResponse(**OrgInviteOut.model_validate(invite).model_dump(), invite_token=raw_token)


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
    items = query.order_by(OrgInvite.created_at.desc()).all()
    return {"items": items}


@router.post("/invites/accept", response_model=OrganizationOut)
def accept_invite(
    payload: OrgInviteAcceptRequest,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    token_hash = _hash_token(payload.token)
    invite = db.query(OrgInvite).filter(OrgInvite.token_hash == token_hash).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    if invite.status == "accepted" or invite.accepted_at:
        raise HTTPException(status_code=400, detail="Invite already accepted")
    now = datetime.now(timezone.utc)
    if invite.expires_at <= now:
        invite.status = "expired"
        db.commit()
        raise HTTPException(status_code=400, detail="Invite expired")

    if user is None:
        if not payload.password:
            raise HTTPException(status_code=401, detail="Password required to create user")
        existing = db.query(User).filter(User.email == invite.invited_email).first()
        if existing:
            raise HTTPException(status_code=401, detail="Login required to accept invite")
        user = User(
            email=invite.invited_email,
            password_hash=get_password_hash(payload.password),
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

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

    org = db.query(Organization).get(invite.organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


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
            created_at=member.created_at,
        )
        for member, user_row in members
    ]


@router.patch("/{org_id}/members/{member_user_id}", response_model=OrgMemberOut)
def update_member_role(
    org_id: int,
    member_user_id: int,
    payload: OrgMemberRoleUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = _require_membership(db, user.id, org_id)
    if membership.role != ROLE_OWNER:
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
        raise HTTPException(status_code=400, detail="Organization must have at least one owner")

    target.role = payload.role.value
    db.commit()

    member_user = db.query(User).get(member_user_id)
    return OrgMemberOut(
        user_id=target.user_id,
        email=member_user.email if member_user else "",
        role=target.role,
        created_at=member_user.created_at if member_user else datetime.now(timezone.utc),
    )


@router.delete("/{org_id}/members/{member_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member(
    org_id: int,
    member_user_id: int,
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
            raise HTTPException(status_code=400, detail="Organization must have at least one owner")
        if membership.role != ROLE_OWNER:
            raise HTTPException(status_code=403, detail="Only owner can remove another owner")

    db.delete(target)
    db.commit()
