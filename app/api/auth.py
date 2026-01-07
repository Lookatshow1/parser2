from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas import (
    AuthRegisterRequest,
    AuthLoginRequest,
    AuthMeResponse,
    AuthTokenResponse,
    AuthRefreshRequest,
    AuthRefreshResponse,
    OrgInviteAcceptRequest,
)
from app.db.models import RefreshToken, User, Organization, Membership, MembershipRole
from app.db.session import get_db
from app.services.auth_service import (
    create_access_token,
    create_refresh_token_data,
    get_password_hash,
    hash_refresh_token,
    verify_password,
)
from app.api.deps import get_current_user
from app.api.orgs import _accept_invite, _hash_token
from app.services.invite_service import get_invite_by_token, resolve_invite_status

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthMeResponse, status_code=status.HTTP_201_CREATED)
def register(payload: AuthRegisterRequest, db: Session = Depends(get_db)):
    email = str(payload.email).strip().lower()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    if payload.invite_token:
        token_hash = _hash_token(payload.invite_token)
        invite = get_invite_by_token(db, token_hash)
        status = resolve_invite_status(invite)
        if status == "not_found":
            raise HTTPException(status_code=400, detail="invite_invalid")
        if status == "expired":
            raise HTTPException(status_code=400, detail="invite_expired")
        if status == "revoked":
            raise HTTPException(status_code=400, detail="invite_revoked")
        if status == "accepted":
            raise HTTPException(status_code=400, detail="invite_already_accepted")
        if invite and email != invite.invited_email:
            raise HTTPException(status_code=400, detail="invite_email_mismatch")

    user = User(
        email=email,
        password_hash=get_password_hash(payload.password),
        is_active=True,
    )
    db.add(user)
    db.flush()

    if payload.invite_token:
        db.commit()
        db.refresh(user)
        _accept_invite(OrgInviteAcceptRequest(token=payload.invite_token), user, db)
        db.refresh(user)
        return user

    org = Organization(name="Personal")
    db.add(org)
    db.flush()

    membership = Membership(
        user_id=user.id,
        organization_id=org.id,
        role=MembershipRole.owner.value,
    )
    db.add(membership)
    user.active_organization_id = org.id

    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=AuthTokenResponse)
def login(payload: AuthLoginRequest, db: Session = Depends(get_db)):
    email = str(payload.email).strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive user")
    access = create_access_token(str(user.id))
    refresh = create_refresh_token_data()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=refresh["token_hash"],
            jti=refresh["jti"],
            expires_at=refresh["expires_at"],
        )
    )
    db.commit()
    return AuthTokenResponse(
        access_token=access["access_token"],
        refresh_token=refresh["raw_token"],
        token_type=access["token_type"],
        expires_in=access["expires_in"],
        refresh_expires_in=refresh["expires_in"],
    )


@router.get("/me", response_model=AuthMeResponse)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/refresh", response_model=AuthRefreshResponse)
def refresh_token(payload: AuthRefreshRequest, db: Session = Depends(get_db)):
    token_hash = hash_refresh_token(payload.refresh_token)
    token = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if not token or token.revoked_at is not None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    now = datetime.now(timezone.utc)
    if token.expires_at <= now:
        raise HTTPException(status_code=401, detail="Refresh token expired")

    user = db.query(User).filter(User.id == token.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive user")

    access = create_access_token(str(user.id))
    return AuthRefreshResponse(**access)
