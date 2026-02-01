"""
Moderation Checker Service.

Checks for ad moderation status changes and sends notifications.
Integrates with sync workers to detect approve/reject events.
"""
import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.models import Organization, Ad, Campaign, Connection
from app.services.telegram_service import get_telegram_service

logger = logging.getLogger(__name__)


# =============================================================================
# MODERATION STATUS CONSTANTS
# =============================================================================

# Yandex Direct moderation statuses
YANDEX_MODERATION_STATUSES = {
    "ACCEPTED": "approved",     # Одобрено
    "REJECTED": "rejected",     # Отклонено
    "MODERATION": "pending",    # На модерации
    "NEW": "draft",             # Новое
}

# VK Ads moderation statuses
VK_MODERATION_STATUSES = {
    "1": "pending",    # На модерации
    "2": "approved",   # Одобрено
    "3": "rejected",   # Отклонено
}

# Normalized statuses
APPROVED_STATUSES = ["approved", "active", "accepted"]
REJECTED_STATUSES = ["rejected", "declined", "banned"]
PENDING_STATUSES = ["pending", "moderation", "draft"]


def normalize_moderation_status(raw_status: str, platform: str = None) -> str:
    """Normalize moderation status to standard values."""
    if not raw_status:
        return "unknown"
    
    raw_lower = raw_status.lower()
    
    # Check if already normalized
    for status in APPROVED_STATUSES:
        if status in raw_lower:
            return "approved"
    for status in REJECTED_STATUSES:
        if status in raw_lower:
            return "rejected"
    for status in PENDING_STATUSES:
        if status in raw_lower:
            return "pending"
    
    # Platform-specific normalization
    if platform == "yandex":
        return YANDEX_MODERATION_STATUSES.get(raw_status.upper(), "unknown")
    elif platform == "vk":
        return VK_MODERATION_STATUSES.get(raw_status, "unknown")
    
    return "unknown"


# =============================================================================
# MODERATION CHECKER
# =============================================================================

class ModerationChecker:
    """
    Service that tracks ad moderation status changes and sends notifications.
    """
    
    def __init__(self, db: Session, organization_id: int):
        self.db = db
        self.organization_id = organization_id
        self._changes: List[Dict] = []
        
    def get_telegram_settings(self) -> Optional[Dict]:
        """Get Telegram settings for the organization."""
        org = self.db.query(Organization).filter(
            Organization.id == self.organization_id
        ).first()
        
        if not org or not org.metadata_json:
            return None
            
        tg_settings = org.metadata_json.get("telegram", {})
        
        if not tg_settings.get("chat_id"):
            return None
            
        if not tg_settings.get("notifications_enabled", True):
            return None
            
        if not tg_settings.get("alert_moderation", True):
            return None
            
        return tg_settings
    
    def check_ad_status_change(
        self,
        ad: Ad,
        old_status: Optional[str],
        new_status: Optional[str],
        platform: str
    ) -> Optional[Dict]:
        """
        Check if moderation status changed and record it.
        
        Returns change record if status changed, None otherwise.
        """
        if old_status == new_status:
            return None
        
        old_normalized = normalize_moderation_status(old_status, platform)
        new_normalized = normalize_moderation_status(new_status, platform)
        
        if old_normalized == new_normalized:
            return None
        
        # Only notify on important transitions
        should_notify = (
            new_normalized in ["approved", "rejected"] or
            (old_normalized in ["approved"] and new_normalized == "rejected") or
            (old_normalized in ["pending"] and new_normalized in ["approved", "rejected"])
        )
        
        if not should_notify:
            return None
        
        # Get campaign name
        campaign_name = None
        if ad.ad_group and ad.ad_group.campaign:
            campaign_name = ad.ad_group.campaign.name
        
        change_record = {
            "ad_id": ad.id,
            "ad_name": ad.name or f"Объявление #{ad.id}",
            "campaign_name": campaign_name or "Неизвестная кампания",
            "platform": platform,
            "old_status": old_normalized,
            "new_status": new_normalized,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        self._changes.append(change_record)
        logger.info(
            f"Moderation status change detected: ad_id={ad.id}, "
            f"{old_normalized} -> {new_normalized}"
        )
        
        return change_record
    
    async def send_notifications(self) -> int:
        """
        Send all pending moderation notifications via Telegram.
        
        Returns number of notifications sent.
        """
        if not self._changes:
            return 0
        
        tg_settings = self.get_telegram_settings()
        if not tg_settings:
            logger.debug("Telegram not configured or moderation alerts disabled")
            return 0
        
        chat_id = tg_settings["chat_id"]
        service = get_telegram_service()
        
        sent_count = 0
        
        try:
            for change in self._changes:
                message = self._format_notification(change)
                result = await service.send_message(chat_id, message)
                
                if result.get("ok"):
                    sent_count += 1
                else:
                    logger.error(
                        f"Failed to send moderation notification: {result.get('error')}"
                    )
        finally:
            await service.close()
        
        # Clear changes after sending
        self._changes.clear()
        
        logger.info(f"Sent {sent_count} moderation notifications")
        return sent_count
    
    def _format_notification(self, change: Dict) -> str:
        """Format moderation change as Telegram message."""
        new_status = change["new_status"]
        
        if new_status == "approved":
            emoji = "✅"
            status_text = "Одобрено"
            description = "Объявление прошло модерацию и теперь показывается аудитории."
        elif new_status == "rejected":
            emoji = "❌"
            status_text = "Отклонено"
            description = "Объявление отклонено модерацией. Проверьте требования платформы."
        else:
            emoji = "⏳"
            status_text = new_status.capitalize()
            description = "Статус модерации изменился."
        
        platform_names = {
            "yandex": "Яндекс",
            "vk": "VK Ads",
            "ozon": "Ozon",
        }
        platform_name = platform_names.get(change["platform"], change["platform"])
        
        return (
            f"📝 <b>Модерация объявления</b>\n\n"
            f"<b>{change['ad_name']}</b>\n"
            f"Кампания: {change['campaign_name']}\n"
            f"Платформа: {platform_name}\n\n"
            f"Статус: {emoji} <b>{status_text}</b>\n\n"
            f"{description}"
        )
    
    def get_changes(self) -> List[Dict]:
        """Get list of detected changes."""
        return self._changes.copy()


# =============================================================================
# BATCH PROCESSING
# =============================================================================

def check_moderation_changes_batch(
    db: Session,
    organization_id: int,
    old_ads_data: Dict[int, str],  # ad_id -> old_status
    new_ads_data: Dict[int, str],  # ad_id -> new_status
    platform: str
) -> List[Dict]:
    """
    Check moderation status changes for a batch of ads.
    
    Args:
        db: Database session
        organization_id: Organization ID
        old_ads_data: Dictionary mapping ad_id to old moderation status
        new_ads_data: Dictionary mapping ad_id to new moderation status
        platform: Platform name (yandex, vk, ozon)
    
    Returns:
        List of change records
    """
    checker = ModerationChecker(db, organization_id)
    
    # Get all ads that might have changed
    changed_ad_ids = set(old_ads_data.keys()) | set(new_ads_data.keys())
    
    ads = db.query(Ad).filter(Ad.id.in_(list(changed_ad_ids))).all()
    ads_by_id = {ad.id: ad for ad in ads}
    
    for ad_id in changed_ad_ids:
        ad = ads_by_id.get(ad_id)
        if not ad:
            continue
        
        old_status = old_ads_data.get(ad_id)
        new_status = new_ads_data.get(ad_id)
        
        checker.check_ad_status_change(ad, old_status, new_status, platform)
    
    return checker.get_changes()


# =============================================================================
# SYNC INTEGRATION
# =============================================================================

async def process_moderation_after_sync(
    db: Session,
    organization_id: int,
    platform: str,
    old_statuses: Dict[int, str],
    new_statuses: Dict[int, str]
) -> int:
    """
    Process moderation changes after sync and send notifications.
    
    Called from sync workers after updating ads.
    
    Returns:
        Number of notifications sent
    """
    checker = ModerationChecker(db, organization_id)
    
    # Get changed ads
    changed_ad_ids = set()
    for ad_id in set(old_statuses.keys()) | set(new_statuses.keys()):
        old = old_statuses.get(ad_id)
        new = new_statuses.get(ad_id)
        if old != new:
            changed_ad_ids.add(ad_id)
    
    if not changed_ad_ids:
        return 0
    
    # Load ads
    ads = db.query(Ad).filter(Ad.id.in_(list(changed_ad_ids))).all()
    
    for ad in ads:
        old_status = old_statuses.get(ad.id)
        new_status = new_statuses.get(ad.id)
        checker.check_ad_status_change(ad, old_status, new_status, platform)
    
    # Send notifications
    return await checker.send_notifications()
