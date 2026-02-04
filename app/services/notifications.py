"""
Real-time Notifications Service.

Multi-channel notifications: Telegram, Email, In-app, Slack.
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import httpx
import logging
import os

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    EMAIL = "email"
    TELEGRAM = "telegram"
    SLACK = "slack"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class NotificationPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Notification:
    """Notification message."""
    title: str
    message: str
    priority: NotificationPriority = NotificationPriority.NORMAL
    channel: NotificationChannel = NotificationChannel.IN_APP
    data: Optional[Dict[str, Any]] = None
    user_id: Optional[int] = None
    organization_id: Optional[int] = None


class NotificationService:
    """
    Multi-channel notification service.
    """
    
    def __init__(self):
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL", "")
        self.smtp_host = os.getenv("SMTP_HOST", "")
        self._client = httpx.AsyncClient(timeout=30.0)
    
    async def send(self, notification: Notification) -> bool:
        """Send notification via specified channel."""
        try:
            if notification.channel == NotificationChannel.TELEGRAM:
                return await self._send_telegram(notification)
            elif notification.channel == NotificationChannel.SLACK:
                return await self._send_slack(notification)
            elif notification.channel == NotificationChannel.EMAIL:
                return await self._send_email(notification)
            elif notification.channel == NotificationChannel.IN_APP:
                return await self._send_in_app(notification)
            elif notification.channel == NotificationChannel.WEBHOOK:
                return await self._send_webhook(notification)
            return False
        except Exception as e:
            logger.exception(f"Failed to send notification: {e}")
            return False
    
    async def send_multi(
        self,
        notification: Notification,
        channels: List[NotificationChannel],
    ) -> Dict[NotificationChannel, bool]:
        """Send notification to multiple channels."""
        results = {}
        for channel in channels:
            notif = Notification(
                title=notification.title,
                message=notification.message,
                priority=notification.priority,
                channel=channel,
                data=notification.data,
                user_id=notification.user_id,
                organization_id=notification.organization_id,
            )
            results[channel] = await self.send(notif)
        return results
    
    async def _send_telegram(self, notification: Notification) -> bool:
        """Send via Telegram Bot API."""
        if not self.telegram_token:
            logger.warning("Telegram token not configured")
            return False
        
        chat_id = notification.data.get("chat_id") if notification.data else None
        if not chat_id:
            logger.warning("No chat_id for Telegram notification")
            return False
        
        # Format message with emoji based on priority
        emoji = {
            NotificationPriority.LOW: "ℹ️",
            NotificationPriority.NORMAL: "📊",
            NotificationPriority.HIGH: "⚠️",
            NotificationPriority.URGENT: "🚨",
        }.get(notification.priority, "📊")
        
        text = f"{emoji} *{notification.title}*\n\n{notification.message}"
        
        response = await self._client.post(
            f"https://api.telegram.org/bot{self.telegram_token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
            },
        )
        
        return response.status_code == 200
    
    async def _send_slack(self, notification: Notification) -> bool:
        """Send via Slack webhook."""
        webhook_url = notification.data.get("webhook_url") if notification.data else self.slack_webhook
        if not webhook_url:
            logger.warning("Slack webhook not configured")
            return False
        
        # Build Slack message with blocks
        color = {
            NotificationPriority.LOW: "#36a64f",
            NotificationPriority.NORMAL: "#2196F3",
            NotificationPriority.HIGH: "#ff9800",
            NotificationPriority.URGENT: "#f44336",
        }.get(notification.priority, "#2196F3")
        
        payload = {
            "attachments": [{
                "color": color,
                "blocks": [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": notification.title},
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": notification.message},
                    },
                    {
                        "type": "context",
                        "elements": [{
                            "type": "mrkdwn",
                            "text": f"Reklai • {datetime.now().strftime('%H:%M')}"
                        }],
                    },
                ],
            }],
        }
        
        response = await self._client.post(webhook_url, json=payload)
        return response.status_code == 200
    
    async def _send_email(self, notification: Notification) -> bool:
        """Send via SMTP."""
        if not self.smtp_host:
            logger.warning("SMTP not configured")
            return False
        
        # Use aiosmtplib in production
        # For now, log the email
        logger.info(f"Email to user {notification.user_id}: {notification.title}")
        return True
    
    async def _send_in_app(self, notification: Notification) -> bool:
        """Store in-app notification in database."""
        # In production, store in notifications table
        # and push via WebSocket
        logger.info(f"In-app notification: {notification.title}")
        return True
    
    async def _send_webhook(self, notification: Notification) -> bool:
        """Send to custom webhook URL."""
        webhook_url = notification.data.get("webhook_url") if notification.data else None
        if not webhook_url:
            return False
        
        payload = {
            "title": notification.title,
            "message": notification.message,
            "priority": notification.priority.value,
            "timestamp": datetime.utcnow().isoformat(),
            "data": notification.data,
        }
        
        response = await self._client.post(webhook_url, json=payload)
        return response.status_code in (200, 201, 202)
    
    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()


# Alert templates
class AlertTemplates:
    """Pre-defined alert templates."""
    
    @staticmethod
    def budget_spent(campaign_name: str, spent: float, budget: float) -> Notification:
        percent = spent / budget * 100 if budget > 0 else 0
        return Notification(
            title="💰 Бюджет израсходован",
            message=f"Кампания *{campaign_name}* израсходовала {percent:.0f}% бюджета ({spent:,.0f}₽ из {budget:,.0f}₽)",
            priority=NotificationPriority.HIGH if percent > 90 else NotificationPriority.NORMAL,
        )
    
    @staticmethod
    def ctr_drop(campaign_name: str, old_ctr: float, new_ctr: float) -> Notification:
        drop = (old_ctr - new_ctr) / old_ctr * 100 if old_ctr > 0 else 0
        return Notification(
            title="📉 Падение CTR",
            message=f"CTR кампании *{campaign_name}* упал на {drop:.1f}% (с {old_ctr:.2f}% до {new_ctr:.2f}%)",
            priority=NotificationPriority.HIGH,
        )
    
    @staticmethod
    def ab_test_winner(test_name: str, winner: str, lift: float) -> Notification:
        return Notification(
            title="🏆 Определён победитель A/B теста",
            message=f"В тесте *{test_name}* победил вариант *{winner}* с преимуществом {lift:.1f}%",
            priority=NotificationPriority.NORMAL,
        )
    
    @staticmethod
    def new_conversion(campaign_name: str, value: float) -> Notification:
        return Notification(
            title="✅ Новая конверсия",
            message=f"Кампания *{campaign_name}*: новая конверсия на сумму {value:,.0f}₽",
            priority=NotificationPriority.LOW,
        )
    
    @staticmethod
    def optimization_applied(actions_count: int) -> Notification:
        return Notification(
            title="⚡ Автооптимизация выполнена",
            message=f"Применено {actions_count} оптимизаций на основе AI-анализа",
            priority=NotificationPriority.NORMAL,
        )
