from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_org
from app.api.schemas import OrgProfileOut, OrgProfileUpdate
from app.db.models import OrgProfile, Organization
from app.db.session import get_db


router = APIRouter()


def _get_or_create_profile(db: Session, org: Organization) -> OrgProfile:
    profile = (
        db.query(OrgProfile)
        .filter(OrgProfile.organization_id == org.id)
        .first()
    )
    if profile:
        return profile
    profile = OrgProfile(
        organization_id=org.id,
        timezone="Europe/Moscow",
        currency="RUB",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/settings/org-profile", response_model=OrgProfileOut)
def get_org_profile(
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    return _get_or_create_profile(db, org)


@router.put("/settings/org-profile", response_model=OrgProfileOut)
def update_org_profile(
    payload: OrgProfileUpdate,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    profile = _get_or_create_profile(db, org)

    if payload.legal_type is not None:
        profile.legal_type = payload.legal_type
    if payload.legal_name is not None:
        profile.legal_name = payload.legal_name
    if payload.inn is not None:
        profile.inn = payload.inn
    if payload.kpp is not None:
        profile.kpp = payload.kpp
    if payload.ogrn is not None:
        profile.ogrn = payload.ogrn
    if payload.ogrnip is not None:
        profile.ogrnip = payload.ogrnip
    if payload.legal_address is not None:
        profile.legal_address = payload.legal_address
    if payload.email_for_docs is not None:
        profile.email_for_docs = payload.email_for_docs
    if payload.phone is not None:
        profile.phone = payload.phone
    if payload.timezone is not None:
        profile.timezone = payload.timezone
    if payload.currency is not None:
        profile.currency = payload.currency

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
