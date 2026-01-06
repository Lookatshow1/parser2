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


def get_current_org(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    x_org_id: int | None = Header(default=None, alias="X-Org-Id"),
) -> Organization:
    org_id = x_org_id or user.active_organization_id
    if not org_id:
        raise HTTPException(status_code=400, detail="Select organization")

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
    return org
