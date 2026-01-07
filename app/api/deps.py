from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.models import Organization, Membership, User
from app.db.session import get_db
from app.services.auth_service import decode_access_token

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    subject = payload.get("sub")
    if not subject:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).get(int(subject))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive user")
    return user


def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User | None:
    if not credentials:
        return None
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid token")
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    subject = payload.get("sub")
    if not subject:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).get(int(subject))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive user")
    return user


def _resolve_org_membership(
    user: User,
    db: Session,
    x_org_id: int | None,
) -> tuple[int, Membership]:
    if x_org_id is not None:
        membership = (
            db.query(Membership)
            .filter(Membership.user_id == user.id, Membership.organization_id == x_org_id)
            .first()
        )
        if not membership:
            raise HTTPException(status_code=403, detail="Forbidden for this organization")
        return x_org_id, membership

    if user.active_organization_id:
        membership = (
            db.query(Membership)
            .filter(
                Membership.user_id == user.id,
                Membership.organization_id == user.active_organization_id,
            )
            .first()
        )
        if membership:
            return user.active_organization_id, membership

    membership = (
        db.query(Membership)
        .filter(Membership.user_id == user.id)
        .order_by(Membership.id.asc())
        .first()
    )
    if not membership:
        raise HTTPException(status_code=409, detail="Select organization")

    user.active_organization_id = membership.organization_id
    db.add(user)
    db.commit()
    db.refresh(user)
    return membership.organization_id, membership


def get_current_org(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    x_org_id: int | None = Header(default=None, alias="X-Org-Id"),
) -> Organization:
    org_id, _membership = _resolve_org_membership(user, db, x_org_id)

    org = db.query(Organization).get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


def get_current_membership(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    x_org_id: int | None = Header(default=None, alias="X-Org-Id"),
) -> Membership:
    _org_id, membership = _resolve_org_membership(user, db, x_org_id)
    return membership
