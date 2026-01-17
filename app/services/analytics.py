"""
Analytics Service

Business logic for aggregating and analyzing campaign metrics.
"""
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.db.models_analytics import CampaignMetrics, AggregatedMetrics


class AnalyticsService:
    """Service for analytics and reporting."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_dashboard_metrics(
        self,
        organization_id: int,
        date_from: date,
        date_to: date,
        platform: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get aggregated metrics for dashboard."""
        
        query = select(
            func.sum(CampaignMetrics.impressions).label("impressions"),
            func.sum(CampaignMetrics.clicks).label("clicks"),
            func.sum(CampaignMetrics.spend).label("spend"),
            func.sum(CampaignMetrics.conversions).label("conversions"),
            func.sum(CampaignMetrics.revenue).label("revenue")
        ).where(
            and_(
                CampaignMetrics.organization_id == organization_id,
                CampaignMetrics.date >= date_from,
                CampaignMetrics.date <= date_to
            )
        )
        
        if platform:
            query = query.where(CampaignMetrics.platform == platform)
        
        result = await self.session.execute(query)
        row = result.one()
        
        impressions = row.impressions or 0
        clicks = row.clicks or 0
        spend = row.spend or 0.0
        conversions = row.conversions or 0
        revenue = row.revenue or 0.0
        
        # Calculate derived metrics
        ctr = (clicks / impressions * 100) if impressions > 0 else 0
        cpc = (spend / clicks) if clicks > 0 else 0
        conversion_rate = (conversions / clicks * 100) if clicks > 0 else 0
        roas = (revenue / spend) if spend > 0 else 0
        
        return {
            "impressions": impressions,
            "clicks": clicks,
            "spend": round(spend, 2),
            "conversions": conversions,
            "revenue": round(revenue, 2),
            "ctr": round(ctr, 2),
            "cpc": round(cpc, 2),
            "conversion_rate": round(conversion_rate, 2),
            "roas": round(roas, 2)
        }
    
    async def get_metrics_timeseries(
        self,
        organization_id: int,
        date_from: date,
        date_to: date,
        metric: str = "impressions",
        platform: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get daily timeseries for a specific metric."""
        
        query = select(
            CampaignMetrics.date,
            func.sum(getattr(CampaignMetrics, metric)).label("value")
        ).where(
            and_(
                CampaignMetrics.organization_id == organization_id,
                CampaignMetrics.date >= date_from,
                CampaignMetrics.date <= date_to
            )
        ).group_by(CampaignMetrics.date).order_by(CampaignMetrics.date)
        
        if platform:
            query = query.where(CampaignMetrics.platform == platform)
        
        result = await self.session.execute(query)
        rows = result.all()
        
        return [
            {"date": row.date.isoformat(), "value": row.value or 0}
            for row in rows
        ]
    
    async def get_platform_breakdown(
        self,
        organization_id: int,
        date_from: date,
        date_to: date
    ) -> List[Dict[str, Any]]:
        """Get metrics breakdown by platform."""
        
        query = select(
            CampaignMetrics.platform,
            func.sum(CampaignMetrics.impressions).label("impressions"),
            func.sum(CampaignMetrics.clicks).label("clicks"),
            func.sum(CampaignMetrics.spend).label("spend"),
            func.sum(CampaignMetrics.conversions).label("conversions"),
            func.sum(CampaignMetrics.revenue).label("revenue")
        ).where(
            and_(
                CampaignMetrics.organization_id == organization_id,
                CampaignMetrics.date >= date_from,
                CampaignMetrics.date <= date_to
            )
        ).group_by(CampaignMetrics.platform)
        
        result = await self.session.execute(query)
        rows = result.all()
        
        return [
            {
                "platform": row.platform,
                "impressions": row.impressions or 0,
                "clicks": row.clicks or 0,
                "spend": round(row.spend or 0, 2),
                "conversions": row.conversions or 0,
                "revenue": round(row.revenue or 0, 2),
                "ctr": round((row.clicks or 0) / (row.impressions or 1) * 100, 2),
                "roas": round((row.revenue or 0) / (row.spend or 1), 2) if row.spend else 0
            }
            for row in rows
        ]
    
    async def compare_periods(
        self,
        organization_id: int,
        current_from: date,
        current_to: date,
        previous_from: date,
        previous_to: date
    ) -> Dict[str, Any]:
        """Compare metrics between two periods (week-over-week, etc)."""
        
        current = await self.get_dashboard_metrics(organization_id, current_from, current_to)
        previous = await self.get_dashboard_metrics(organization_id, previous_from, previous_to)
        
        def calc_change(current_val, previous_val):
            if previous_val == 0:
                return 100 if current_val > 0 else 0
            return round((current_val - previous_val) / previous_val * 100, 1)
        
        return {
            "current": current,
            "previous": previous,
            "changes": {
                "impressions": calc_change(current["impressions"], previous["impressions"]),
                "clicks": calc_change(current["clicks"], previous["clicks"]),
                "spend": calc_change(current["spend"], previous["spend"]),
                "conversions": calc_change(current["conversions"], previous["conversions"]),
                "ctr": calc_change(current["ctr"], previous["ctr"]),
                "roas": calc_change(current["roas"], previous["roas"]),
            }
        }
    
    async def seed_demo_data(self, organization_id: int):
        """Generate demo analytics data for testing."""
        import random
        
        today = date.today()
        platforms = ["yandex", "google", "vk"]
        
        for days_ago in range(30):
            current_date = today - timedelta(days=days_ago)
            
            for platform in platforms:
                impressions = random.randint(1000, 10000)
                clicks = int(impressions * random.uniform(0.02, 0.08))
                spend = clicks * random.uniform(15, 50)
                conversions = int(clicks * random.uniform(0.05, 0.15))
                revenue = conversions * random.uniform(500, 2000)
                
                metric = CampaignMetrics(
                    organization_id=organization_id,
                    platform=platform,
                    date=current_date,
                    impressions=impressions,
                    clicks=clicks,
                    spend=round(spend, 2),
                    conversions=conversions,
                    revenue=round(revenue, 2),
                    ctr=round(clicks / impressions * 100, 2) if impressions else 0,
                    cpc=round(spend / clicks, 2) if clicks else 0,
                    conversion_rate=round(conversions / clicks * 100, 2) if clicks else 0,
                    roas=round(revenue / spend, 2) if spend else 0
                )
                self.session.add(metric)
        
        await self.session.commit()
