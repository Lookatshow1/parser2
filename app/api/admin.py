"""
Admin API Endpoints

Protected endpoints for admin panel.
Credentials: admin / admin
"""
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel

from app.api.deps import get_db
from app.db.models import User, Organization, Membership
from app.db.models_drafts import DraftCampaign, DraftAd
from app.db.models_billing import BillingAccount, BillingTransaction

router = APIRouter(prefix="/admin", tags=["Admin"])

# Admin credentials (in production, use env vars)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

# Simple token storage (in production, use Redis or DB)
_admin_tokens = {}


# =============================================================================
# SCHEMAS
# =============================================================================

class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    token: str
    expires_at: str


class DashboardStats(BaseModel):
    total_users: int
    new_users_today: int
    new_users_week: int
    total_organizations: int
    total_campaigns: int
    active_campaigns: int
    total_balance: float
    total_spent: float
    avg_roas: float


class UserSummary(BaseModel):
    id: int
    email: str
    created_at: str
    campaigns_count: int
    total_spent: float
    balance: float
    is_active: bool


class SystemSettings(BaseModel):
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    ai_model: str = "gpt-4o-mini"
    ai_temperature: float = 0.7
    registration_enabled: bool = True


# =============================================================================
# AUTH
# =============================================================================

def verify_admin_token(x_admin_token: str = Header(None, alias="X-Admin-Token")):
    """Verify admin token from header."""
    if not x_admin_token:
        raise HTTPException(status_code=401, detail="Admin token required")
    
    token_data = _admin_tokens.get(x_admin_token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid admin token")
    
    if datetime.utcnow() > token_data["expires_at"]:
        del _admin_tokens[x_admin_token]
        raise HTTPException(status_code=401, detail="Token expired")
    
    return True


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(payload: AdminLoginRequest):
    """Admin login endpoint."""
    if payload.username != ADMIN_USERNAME or payload.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Generate token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    _admin_tokens[token] = {
        "username": payload.username,
        "expires_at": expires_at
    }
    
    return AdminLoginResponse(
        token=token,
        expires_at=expires_at.isoformat()
    )


@router.post("/logout")
async def admin_logout(x_admin_token: str = Header(None, alias="X-Admin-Token")):
    """Admin logout endpoint."""
    if x_admin_token and x_admin_token in _admin_tokens:
        del _admin_tokens[x_admin_token]
    return {"message": "Logged out"}


# =============================================================================
# DASHBOARD
# =============================================================================

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_token)
):
    """Get admin dashboard statistics."""
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    
    # Users
    total_users = db.query(func.count(User.id)).scalar() or 0
    new_users_today = db.query(func.count(User.id)).filter(
        func.date(User.created_at) == today
    ).scalar() or 0
    new_users_week = db.query(func.count(User.id)).filter(
        func.date(User.created_at) >= week_ago
    ).scalar() or 0
    
    # Organizations
    total_orgs = db.query(func.count(Organization.id)).scalar() or 0
    
    # Campaigns
    total_campaigns = db.query(func.count(DraftCampaign.id)).scalar() or 0
    active_campaigns = db.query(func.count(DraftCampaign.id)).filter(
        DraftCampaign.status == "published"
    ).scalar() or 0
    
    # Finances
    total_balance = db.query(func.sum(BillingAccount.balance)).scalar() or 0.0
    total_spent = db.query(func.sum(BillingTransaction.amount)).filter(
        BillingTransaction.type == "spend"
    ).scalar() or 0.0
    
    return DashboardStats(
        total_users=total_users,
        new_users_today=new_users_today,
        new_users_week=new_users_week,
        total_organizations=total_orgs,
        total_campaigns=total_campaigns,
        active_campaigns=active_campaigns,
        total_balance=float(total_balance),
        total_spent=float(abs(total_spent)),
        avg_roas=4.2  # Mock for now
    )


# =============================================================================
# USERS
# =============================================================================

@router.get("/users")
async def list_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_token)
):
    """List all users with stats."""
    users = db.query(User).order_by(desc(User.created_at)).offset(skip).limit(limit).all()
    
    result = []
    for user in users:
        # Get user's campaigns count
        campaigns_count = db.query(func.count(DraftCampaign.id)).join(
            Organization, DraftCampaign.organization_id == Organization.id
        ).join(
            Membership, Membership.organization_id == Organization.id
        ).filter(Membership.user_id == user.id).scalar() or 0
        
        # Get user's balance
        balance = 0.0
        membership = db.query(Membership).filter(Membership.user_id == user.id).first()
        if membership:
            account = db.query(BillingAccount).filter(
                BillingAccount.organization_id == membership.organization_id
            ).first()
            if account:
                balance = account.balance or 0.0
        
        result.append({
            "id": user.id,
            "email": user.email,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "campaigns_count": campaigns_count,
            "total_spent": 0.0,  # TODO: calculate
            "balance": balance,
            "is_active": user.is_active
        })
    
    total = db.query(func.count(User.id)).scalar() or 0
    
    return {
        "items": result,
        "total": total
    }


@router.post("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_token)
):
    """Toggle user active status."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = not user.is_active
    db.commit()
    
    return {"id": user.id, "is_active": user.is_active}


# =============================================================================
# SETTINGS
# =============================================================================

# In-memory settings (in production, use DB or config file)
_system_settings = {
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
    "ai_model": "gpt-4o-mini",
    "ai_temperature": 0.7,
    "registration_enabled": True
}


@router.get("/settings", response_model=SystemSettings)
async def get_settings(_: bool = Depends(verify_admin_token)):
    """Get system settings."""
    # Mask API keys
    settings = _system_settings.copy()
    if settings["openai_api_key"]:
        settings["openai_api_key"] = settings["openai_api_key"][:8] + "..." + settings["openai_api_key"][-4:]
    if settings["anthropic_api_key"]:
        settings["anthropic_api_key"] = settings["anthropic_api_key"][:8] + "..." + settings["anthropic_api_key"][-4:]
    
    return SystemSettings(**settings)


@router.put("/settings")
async def update_settings(
    payload: SystemSettings,
    _: bool = Depends(verify_admin_token)
):
    """Update system settings."""
    if payload.openai_api_key and not payload.openai_api_key.endswith("..."):
        _system_settings["openai_api_key"] = payload.openai_api_key
        os.environ["OPENAI_API_KEY"] = payload.openai_api_key
    
    if payload.anthropic_api_key and not payload.anthropic_api_key.endswith("..."):
        _system_settings["anthropic_api_key"] = payload.anthropic_api_key
        os.environ["ANTHROPIC_API_KEY"] = payload.anthropic_api_key
    
    _system_settings["ai_model"] = payload.ai_model
    _system_settings["ai_temperature"] = payload.ai_temperature
    _system_settings["registration_enabled"] = payload.registration_enabled
    
    return {"message": "Settings updated"}


# =============================================================================
# FINANCES
# =============================================================================

@router.get("/transactions")
async def list_transactions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_token)
):
    """List all transactions."""
    transactions = db.query(BillingTransaction).order_by(
        desc(BillingTransaction.created_at)
    ).offset(skip).limit(limit).all()
    
    result = []
    for tx in transactions:
        result.append({
            "id": tx.id,
            "organization_id": tx.organization_id,
            "type": tx.type,
            "amount": tx.amount,
            "status": tx.status,
            "description": tx.description,
            "created_at": tx.created_at.isoformat() if tx.created_at else None
        })
    
    total = db.query(func.count(BillingTransaction.id)).scalar() or 0
    total_amount = db.query(func.sum(BillingTransaction.amount)).filter(
        BillingTransaction.type == "topup"
    ).scalar() or 0
    
    return {
        "items": result,
        "total": total,
        "total_topup": float(total_amount)
    }


# =============================================================================
# CAMPAIGN STATS
# =============================================================================

@router.get("/campaign-stats")
async def get_campaign_stats(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_token)
):
    """Get campaign statistics by platform."""
    # Stats by platform
    platforms = db.query(
        DraftCampaign.platform,
        func.count(DraftCampaign.id).label("count")
    ).group_by(DraftCampaign.platform).all()
    
    by_platform = {p.platform: p.count for p in platforms}
    
    # Stats by status
    statuses = db.query(
        DraftCampaign.status,
        func.count(DraftCampaign.id).label("count")
    ).group_by(DraftCampaign.status).all()
    
    by_status = {s.status: s.count for s in statuses}
    
    # Recent campaigns
    recent = db.query(DraftCampaign).order_by(
        desc(DraftCampaign.created_at)
    ).limit(10).all()
    
    return {
        "by_platform": by_platform,
        "by_status": by_status,
        "recent": [
            {
                "id": c.id,
                "name": c.name,
                "platform": c.platform,
                "status": c.status,
                "created_at": c.created_at.isoformat() if c.created_at else None
            }
            for c in recent
        ],
        "total_ads": db.query(func.count(DraftAd.id)).scalar() or 0
    }
