"""
Telegram Notification Service.

Send alerts and reports to Telegram chats/channels.
"""
import os
import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

TELEGRAM_API_BASE = "https://api.telegram.org"


def get_bot_token() -> str:
    """Get Telegram bot token from env or admin settings."""
    return os.getenv("TELEGRAM_BOT_TOKEN", "")


def get_admin_chat_id() -> str:
    """Get admin chat ID for system notifications."""
    return os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")


# =============================================================================
# TELEGRAM SERVICE
# =============================================================================

class TelegramService:
    """Service for sending Telegram notifications."""
    
    def __init__(self, bot_token: Optional[str] = None):
        self.bot_token = bot_token or get_bot_token()
        self._client = httpx.AsyncClient(timeout=30.0)
    
    @property
    def is_configured(self) -> bool:
        """Check if Telegram is properly configured."""
        return bool(self.bot_token)
    
    async def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "HTML",
        disable_notification: bool = False,
    ) -> dict:
        """
        Send a text message to a chat.
        
        Args:
            chat_id: Telegram chat ID
            text: Message text (HTML or Markdown)
            parse_mode: HTML or Markdown
            disable_notification: Send silently
            
        Returns:
            Telegram API response
        """
        if not self.is_configured:
            logger.warning("Telegram not configured, skipping message")
            return {"ok": False, "error": "Not configured"}
        
        url = f"{TELEGRAM_API_BASE}/bot{self.bot_token}/sendMessage"
        
        try:
            response = await self._client.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": parse_mode,
                    "disable_notification": disable_notification,
                }
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.exception(f"Failed to send Telegram message: {e}")
            return {"ok": False, "error": str(e)}
    
    # -------------------------------------------------------------------------
    # Alert Types
    # -------------------------------------------------------------------------
    
    async def send_budget_alert(
        self,
        chat_id: str,
        campaign_name: str,
        budget_remaining: float,
        budget_total: float,
    ):
        """Alert: Budget is running low."""
        percent = (budget_remaining / budget_total * 100) if budget_total > 0 else 0
        
        text = f"""
⚠️ <b>Бюджет заканчивается</b>

📊 Кампания: <b>{campaign_name}</b>
💰 Остаток: <b>₽{budget_remaining:,.0f}</b> из ₽{budget_total:,.0f}
📉 Осталось: <b>{percent:.1f}%</b>

<i>Рекомендуем пополнить бюджет для продолжения показов.</i>
"""
        return await self.send_message(chat_id, text.strip())
    
    async def send_ctr_alert(
        self,
        chat_id: str,
        ad_title: str,
        current_ctr: float,
        previous_ctr: float,
    ):
        """Alert: CTR dropped significantly."""
        drop = ((previous_ctr - current_ctr) / previous_ctr * 100) if previous_ctr > 0 else 0
        
        text = f"""
📉 <b>CTR упал</b>

📝 Объявление: <b>{ad_title}</b>
📊 CTR: <b>{current_ctr:.2f}%</b> (было {previous_ctr:.2f}%)
⬇️ Падение: <b>{drop:.1f}%</b>

<i>Рассмотрите изменение заголовка или текста объявления.</i>
"""
        return await self.send_message(chat_id, text.strip())
    
    async def send_conversion_alert(
        self,
        chat_id: str,
        goal_name: str,
        campaign_name: str,
        conversion_value: Optional[float] = None,
    ):
        """Alert: New conversion achieved."""
        value_text = f" (₽{conversion_value:,.0f})" if conversion_value else ""
        
        text = f"""
🎯 <b>Новая конверсия!</b>

✅ Цель: <b>{goal_name}</b>{value_text}
📊 Кампания: {campaign_name}
"""
        return await self.send_message(chat_id, text.strip())
    
    async def send_daily_report(
        self,
        chat_id: str,
        impressions: int,
        clicks: int,
        spend: float,
        conversions: int,
        ctr: float,
        cpc: float,
    ):
        """Send daily performance report."""
        text = f"""
📊 <b>Ежедневный отчёт</b>

👁 Показы: <b>{impressions:,}</b>
👆 Клики: <b>{clicks:,}</b>
💰 Расход: <b>₽{spend:,.0f}</b>
🎯 Конверсии: <b>{conversions}</b>

📈 CTR: <b>{ctr:.2f}%</b>
💵 CPC: <b>₽{cpc:.0f}</b>
"""
        return await self.send_message(chat_id, text.strip())
    
    async def send_weekly_report(
        self,
        chat_id: str,
        summary: dict,
    ):
        """Send weekly performance summary."""
        text = f"""
📈 <b>Еженедельный отчёт</b>

💰 Расход: <b>₽{summary.get('spend', 0):,.0f}</b>
🎯 Конверсии: <b>{summary.get('conversions', 0)}</b>
📊 ROI: <b>{summary.get('roi', 0):.1f}%</b>

<b>Топ кампании:</b>
{summary.get('top_campaigns_text', 'Нет данных')}

<i>Подробнее в личном кабинете.</i>
"""
        return await self.send_message(chat_id, text.strip())
    
    async def send_admin_notification(
        self,
        text: str,
    ):
        """Send notification to admin chat."""
        admin_chat = get_admin_chat_id()
        if not admin_chat:
            logger.warning("Admin chat ID not configured")
            return {"ok": False, "error": "Admin chat not configured"}
        
        return await self.send_message(admin_chat, text)
    
    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()


# =============================================================================
# FACTORY
# =============================================================================

def get_telegram_service() -> TelegramService:
    """Get Telegram service instance."""
    return TelegramService()
