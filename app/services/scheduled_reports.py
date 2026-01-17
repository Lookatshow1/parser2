"""
Scheduled Reports Service.

Automated report generation and delivery.
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models import User, Organization, Connection
from app.db.models_drafts import DraftCampaign
from app.services.notifications import NotificationService, Notification, NotificationChannel, NotificationPriority

logger = logging.getLogger(__name__)


class ReportFrequency(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ReportType(Enum):
    EXECUTIVE_SUMMARY = "executive_summary"
    PERFORMANCE = "performance"
    BUDGET = "budget"
    ANOMALIES = "anomalies"
    COMPETITOR_WATCH = "competitor_watch"


@dataclass
class ReportConfig:
    """Report configuration."""
    report_type: ReportType
    frequency: ReportFrequency
    channels: List[NotificationChannel]
    recipients: List[str]  # emails or chat IDs
    enabled: bool = True


@dataclass
class ReportData:
    """Generated report data."""
    title: str
    period: str
    sections: List[Dict[str, Any]]
    generated_at: datetime


class ScheduledReports:
    """
    Automated report generation and delivery.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.notifications = NotificationService()
    
    async def generate_executive_summary(
        self,
        organization_id: int,
        period_days: int = 7,
    ) -> ReportData:
        """Generate executive summary report."""
        # Get organization
        org = self.db.query(Organization).filter(
            Organization.id == organization_id
        ).first()
        
        if not org:
            raise ValueError("Organization not found")
        
        # Calculate period
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        period_str = f"{start_date.strftime('%d.%m')} - {end_date.strftime('%d.%m.%Y')}"
        
        # Gather metrics
        campaigns = self.db.query(DraftCampaign).filter(
            DraftCampaign.organization_id == organization_id
        ).all()
        
        connections = self.db.query(Connection).filter(
            Connection.organization_id == organization_id,
            Connection.is_active == True
        ).count()
        
        # Build sections
        sections = [
            {
                "title": "📊 Обзор",
                "items": [
                    {"label": "Активных кампаний", "value": len(campaigns)},
                    {"label": "Подключённых кабинетов", "value": connections},
                    {"label": "Период", "value": period_str},
                ],
            },
            {
                "title": "💰 Бюджет",
                "items": [
                    {"label": "Общий расход", "value": "₽ —"},
                    {"label": "Средний CPC", "value": "—"},
                    {"label": "ROAS", "value": "—"},
                ],
            },
            {
                "title": "📈 Трафик",
                "items": [
                    {"label": "Показы", "value": "—"},
                    {"label": "Клики", "value": "—"},
                    {"label": "CTR", "value": "—"},
                ],
            },
            {
                "title": "🎯 Конверсии",
                "items": [
                    {"label": "Всего", "value": "—"},
                    {"label": "CVR", "value": "—"},
                    {"label": "CPA", "value": "—"},
                ],
            },
        ]
        
        return ReportData(
            title=f"Еженедельный отчёт: {org.name}",
            period=period_str,
            sections=sections,
            generated_at=datetime.utcnow(),
        )
    
    async def send_report(
        self,
        report: ReportData,
        channels: List[NotificationChannel],
        recipients: Dict[NotificationChannel, List[str]],
    ):
        """Send report to recipients via specified channels."""
        # Format report as text
        text_parts = [f"📊 *{report.title}*", f"Период: {report.period}", ""]
        
        for section in report.sections:
            text_parts.append(f"*{section['title']}*")
            for item in section.get("items", []):
                text_parts.append(f"• {item['label']}: {item['value']}")
            text_parts.append("")
        
        message_text = "\n".join(text_parts)
        
        # Send via each channel
        for channel in channels:
            channel_recipients = recipients.get(channel, [])
            
            for recipient in channel_recipients:
                notification = Notification(
                    title=report.title,
                    message=message_text,
                    priority=NotificationPriority.NORMAL,
                    channel=channel,
                    data={"chat_id": recipient} if channel == NotificationChannel.TELEGRAM else {"email": recipient},
                )
                
                await self.notifications.send(notification)
    
    async def close(self):
        """Close services."""
        await self.notifications.close()


class ReportTemplates:
    """Pre-built report templates."""
    
    @staticmethod
    def format_telegram_report(report: ReportData) -> str:
        """Format report for Telegram."""
        lines = [
            f"📊 *{report.title}*",
            f"📅 {report.period}",
            "",
        ]
        
        for section in report.sections:
            lines.append(f"*{section['title']}*")
            for item in section.get("items", []):
                lines.append(f"  • {item['label']}: `{item['value']}`")
            lines.append("")
        
        lines.append("_Сгенерировано Effecto_")
        return "\n".join(lines)
    
    @staticmethod
    def format_slack_blocks(report: ReportData) -> List[Dict]:
        """Format report as Slack blocks."""
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": report.title},
            },
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": f"📅 {report.period}"}],
            },
            {"type": "divider"},
        ]
        
        for section in report.sections:
            fields = []
            for item in section.get("items", []):
                fields.append({
                    "type": "mrkdwn",
                    "text": f"*{item['label']}*\n{item['value']}",
                })
            
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": section["title"]},
            })
            
            if fields:
                blocks.append({
                    "type": "section",
                    "fields": fields[:10],  # Slack limit
                })
        
        return blocks
    
    @staticmethod
    def format_email_html(report: ReportData) -> str:
        """Format report as HTML email."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #7c3aed, #db2777); color: white; padding: 30px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .period {{ color: rgba(255,255,255,0.8); margin-top: 10px; }}
        .content {{ padding: 30px; }}
        .section {{ margin-bottom: 25px; }}
        .section-title {{ font-size: 16px; font-weight: 600; color: #333; margin-bottom: 15px; }}
        .item {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }}
        .item-label {{ color: #666; }}
        .item-value {{ font-weight: 600; color: #333; }}
        .footer {{ text-align: center; padding: 20px; color: #999; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{report.title}</h1>
            <div class="period">{report.period}</div>
        </div>
        <div class="content">
"""
        
        for section in report.sections:
            html += f'<div class="section">\n'
            html += f'<div class="section-title">{section["title"]}</div>\n'
            for item in section.get("items", []):
                html += f'''
<div class="item">
    <span class="item-label">{item["label"]}</span>
    <span class="item-value">{item["value"]}</span>
</div>
'''
            html += '</div>\n'
        
        html += """
        </div>
        <div class="footer">
            Сгенерировано Effecto • effecto.ai
        </div>
    </div>
</body>
</html>
"""
        return html
