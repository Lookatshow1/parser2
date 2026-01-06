from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.schemas import (
    OrganizationCreateRequest,
    OrganizationListResponse,
    OrganizationOut,
    OrganizationSwitchRequest,
)
from app.db.models import Membership, MembershipRole, Organization, User
from app.db.session import get_db

router = APIRouter(prefix="/orgs", tags=["orgs"])


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
        raise HTTPException(status_code=404, detail="Active organization not set")
    org = db.query(Organization).get(user.active_organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
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
