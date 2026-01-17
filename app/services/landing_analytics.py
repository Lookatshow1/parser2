"""
Landing Page Analytics.

Track user behavior on landing pages for optimization.
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    PAGE_VIEW = "page_view"
    SCROLL = "scroll"
    CLICK = "click"
    FORM_START = "form_start"
    FORM_SUBMIT = "form_submit"
    LEAD = "lead"
    SALE = "sale"
    BOUNCE = "bounce"


@dataclass
class AnalyticsEvent:
    """Single analytics event."""
    event_type: EventType
    timestamp: datetime
    session_id: str
    user_id: Optional[str] = None
    page_url: str = ""
    referrer: str = ""
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


@dataclass
class FunnelStep:
    """Funnel step metrics."""
    name: str
    event_type: EventType
    count: int
    conversion_rate: float  # From previous step


@dataclass
class LandingAnalytics:
    """Landing page analytics summary."""
    page_url: str
    period_start: datetime
    period_end: datetime
    
    # Traffic
    total_visits: int = 0
    unique_visitors: int = 0
    bounce_rate: float = 0.0
    avg_time_on_page: float = 0.0
    
    # Conversions
    leads: int = 0
    lead_rate: float = 0.0
    sales: int = 0
    conversion_rate: float = 0.0
    
    # Sources
    traffic_sources: Dict[str, int] = None
    campaigns: Dict[str, int] = None
    
    # Device
    device_breakdown: Dict[str, int] = None


class LandingAnalyticsService:
    """
    Landing page analytics service.
    
    Tracks visitor behavior, conversions, and funnel analysis.
    """
    
    def __init__(self):
        self._events: List[AnalyticsEvent] = []
    
    def track_event(self, event: AnalyticsEvent):
        """Track an analytics event."""
        self._events.append(event)
        logger.debug(f"Tracked event: {event.event_type.value} on {event.page_url}")
    
    def get_landing_analytics(
        self,
        page_url: str,
        period_days: int = 7,
    ) -> LandingAnalytics:
        """Get analytics for a landing page."""
        now = datetime.utcnow()
        start = now - timedelta(days=period_days)
        
        # Filter events for this page and period
        page_events = [
            e for e in self._events
            if e.page_url == page_url and e.timestamp >= start
        ]
        
        if not page_events:
            return LandingAnalytics(
                page_url=page_url,
                period_start=start,
                period_end=now,
            )
        
        # Calculate metrics
        sessions = set(e.session_id for e in page_events)
        visitors = set(e.user_id for e in page_events if e.user_id)
        
        page_views = [e for e in page_events if e.event_type == EventType.PAGE_VIEW]
        bounces = [e for e in page_events if e.event_type == EventType.BOUNCE]
        leads = [e for e in page_events if e.event_type == EventType.LEAD]
        sales = [e for e in page_events if e.event_type == EventType.SALE]
        
        total_visits = len(page_views)
        
        # Traffic sources
        sources = {}
        campaigns = {}
        for e in page_views:
            source = e.utm_source or "direct"
            sources[source] = sources.get(source, 0) + 1
            
            if e.utm_campaign:
                campaigns[e.utm_campaign] = campaigns.get(e.utm_campaign, 0) + 1
        
        return LandingAnalytics(
            page_url=page_url,
            period_start=start,
            period_end=now,
            total_visits=total_visits,
            unique_visitors=len(visitors) or len(sessions),
            bounce_rate=(len(bounces) / total_visits * 100) if total_visits > 0 else 0,
            leads=len(leads),
            lead_rate=(len(leads) / total_visits * 100) if total_visits > 0 else 0,
            sales=len(sales),
            conversion_rate=(len(sales) / total_visits * 100) if total_visits > 0 else 0,
            traffic_sources=sources,
            campaigns=campaigns,
        )
    
    def build_funnel(
        self,
        page_url: str,
        steps: List[EventType],
        period_days: int = 7,
    ) -> List[FunnelStep]:
        """Build conversion funnel."""
        now = datetime.utcnow()
        start = now - timedelta(days=period_days)
        
        page_events = [
            e for e in self._events
            if e.page_url == page_url and e.timestamp >= start
        ]
        
        funnel = []
        previous_count = None
        
        step_names = {
            EventType.PAGE_VIEW: "Просмотр страницы",
            EventType.SCROLL: "Скролл 50%",
            EventType.CLICK: "Клик на CTA",
            EventType.FORM_START: "Начало заполнения формы",
            EventType.FORM_SUBMIT: "Отправка формы",
            EventType.LEAD: "Лид",
            EventType.SALE: "Продажа",
        }
        
        for step_type in steps:
            count = sum(1 for e in page_events if e.event_type == step_type)
            
            if previous_count is None:
                rate = 100.0
            elif previous_count == 0:
                rate = 0.0
            else:
                rate = count / previous_count * 100
            
            funnel.append(FunnelStep(
                name=step_names.get(step_type, step_type.value),
                event_type=step_type,
                count=count,
                conversion_rate=round(rate, 2),
            ))
            
            previous_count = count
        
        return funnel
    
    def get_top_converting_sources(
        self,
        page_url: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get top converting traffic sources."""
        page_events = [e for e in self._events if e.page_url == page_url]
        
        # Group by source
        source_data = {}
        for e in page_events:
            source = e.utm_source or "direct"
            if source not in source_data:
                source_data[source] = {"visits": 0, "leads": 0, "sales": 0}
            
            if e.event_type == EventType.PAGE_VIEW:
                source_data[source]["visits"] += 1
            elif e.event_type == EventType.LEAD:
                source_data[source]["leads"] += 1
            elif e.event_type == EventType.SALE:
                source_data[source]["sales"] += 1
        
        # Calculate conversion rates
        results = []
        for source, data in source_data.items():
            visits = data["visits"]
            results.append({
                "source": source,
                "visits": visits,
                "leads": data["leads"],
                "sales": data["sales"],
                "lead_rate": (data["leads"] / visits * 100) if visits > 0 else 0,
                "conversion_rate": (data["sales"] / visits * 100) if visits > 0 else 0,
            })
        
        # Sort by conversion rate
        results.sort(key=lambda x: x["conversion_rate"], reverse=True)
        return results[:limit]
