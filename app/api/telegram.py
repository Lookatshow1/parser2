"""
Telegram Notifications API Endpoints.

Manage Telegram bot settings and test notifications.
Client-side integration in user's personal account.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.api.deps import get_db, get_current_user, get_current_org_id
from app.db.models import User, Organization
from app.services.telegram_service import get_telegram_service

router = APIRouter(prefix="/telegram", tags=["Telegram"])


# =============================================================================
# SCHEMAS
# =============================================================================

class TelegramConnectRequest(BaseModel):
    """Connect Telegram chat to organization."""
    chat_id: str


class TelegramSettingsResponse(BaseModel):
    """Telegram settings for organization."""
    connected: bool
    chat_id: Optional[str] = None
    notifications_enabled: bool = True
    alert_budget: bool = True
    alert_ctr: bool = True
    alert_conversions: bool = True
    alert_moderation: bool = True
    daily_report: bool = False
    weekly_report: bool = True


class TelegramSettingsUpdate(BaseModel):
    """Update notification preferences."""
    notifications_enabled: bool = True
    alert_budget: bool = True
    alert_ctr: bool = True
    alert_conversions: bool = True
    alert_moderation: bool = True
    daily_report: bool = False
    weekly_report: bool = True


class TestNotificationRequest(BaseModel):
    """Test notification request."""
    type: str = "test"  # test, budget, ctr, conversion, moderation, daily


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/settings", response_model=TelegramSettingsResponse)
def get_telegram_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: int = Depends(get_current_org_id),
):
    """Get Telegram settings for current organization."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    
    if not org or not org.metadata_json:
        return TelegramSettingsResponse(connected=False)
    
    tg_settings = org.metadata_json.get("telegram", {})
    
    return TelegramSettingsResponse(
        connected=bool(tg_settings.get("chat_id")),
        chat_id=tg_settings.get("chat_id", "")[:4] + "..." if tg_settings.get("chat_id") else None,
        notifications_enabled=tg_settings.get("notifications_enabled", True),
        alert_budget=tg_settings.get("alert_budget", True),
        alert_ctr=tg_settings.get("alert_ctr", True),
        alert_conversions=tg_settings.get("alert_conversions", True),
        alert_moderation=tg_settings.get("alert_moderation", True),
        daily_report=tg_settings.get("daily_report", False),
        weekly_report=tg_settings.get("weekly_report", True),
    )


@router.post("/connect")
def connect_telegram(
    payload: TelegramConnectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: int = Depends(get_current_org_id),
):
    """
    Connect Telegram chat to organization.
    
    User gets chat_id by messaging the bot and running /start.
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    if not org.metadata_json:
        org.metadata_json = {}
    
    org.metadata_json["telegram"] = {
        "chat_id": payload.chat_id,
        "notifications_enabled": True,
        "alert_budget": True,
        "alert_ctr": True,
        "alert_conversions": True,
        "alert_moderation": True,
        "daily_report": False,
        "weekly_report": True,
    }
    db.commit()
    
    return {"connected": True, "message": "Telegram подключён"}


@router.put("/settings")
def update_telegram_settings(
    payload: TelegramSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: int = Depends(get_current_org_id),
):
    """Update notification preferences."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    if not org.metadata_json or "telegram" not in org.metadata_json:
        raise HTTPException(status_code=400, detail="Telegram not connected")
    
    tg = org.metadata_json["telegram"]
    tg["notifications_enabled"] = payload.notifications_enabled
    tg["alert_budget"] = payload.alert_budget
    tg["alert_ctr"] = payload.alert_ctr
    tg["alert_conversions"] = payload.alert_conversions
    tg["alert_moderation"] = payload.alert_moderation
    tg["daily_report"] = payload.daily_report
    tg["weekly_report"] = payload.weekly_report
    
    db.commit()
    
    return {"message": "Настройки обновлены"}


@router.delete("/disconnect")
def disconnect_telegram(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: int = Depends(get_current_org_id),
):
    """Disconnect Telegram from organization."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    if org.metadata_json and "telegram" in org.metadata_json:
        del org.metadata_json["telegram"]
        db.commit()
    
    return {"connected": False, "message": "Telegram отключён"}


@router.post("/test")
async def send_test_notification(
    payload: TestNotificationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: int = Depends(get_current_org_id),
):
    """Send test notification to connected Telegram chat."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org or not org.metadata_json:
        raise HTTPException(status_code=400, detail="Telegram not connected")
    
    tg_settings = org.metadata_json.get("telegram", {})
    chat_id = tg_settings.get("chat_id")
    
    if not chat_id:
        raise HTTPException(status_code=400, detail="Telegram not connected")
    
    service = get_telegram_service()
    
    if payload.type == "budget":
        result = await service.send_budget_alert(chat_id, "Тестовая кампания", 1500, 10000)
    elif payload.type == "ctr":
        result = await service.send_ctr_alert(chat_id, "Тестовое объявление", 1.2, 2.5)
    elif payload.type == "conversion":
        result = await service.send_conversion_alert(chat_id, "Покупка", "Тестовая кампания", 5000)
    elif payload.type == "moderation":
        result = await service.send_message(
            chat_id,
            "📝 <b>Модерация объявления</b>\n\n"
            "Объявление: <b>Тестовое объявление</b>\n"
            "Кампания: Тестовая кампания\n"
            "Статус: ✅ <b>Одобрено</b>\n\n"
            "Теперь объявление активно и показывается аудитории."
        )
    elif payload.type == "daily":
        result = await service.send_daily_report(chat_id, 45000, 1200, 35000, 45, 2.67, 29)
    else:
        result = await service.send_message(
            chat_id, 
            "✅ <b>Тестовое уведомление</b>\n\nEffecto подключён и работает!"
        )
    
    await service.close()
    
    if result.get("ok"):
        return {"success": True, "message": "Уведомление отправлено"}
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to send"))
