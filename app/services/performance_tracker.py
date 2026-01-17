"""
Performance Tracking Service.

Real-time campaign performance metrics and alerts.
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TrendDirection(Enum):
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


@dataclass
class MetricPoint:
    """Single metric data point."""
    timestamp: datetime
    value: float


@dataclass
class PerformanceTrend:
    """Performance trend analysis."""
    metric_name: str
    current_value: float
    previous_value: float
    change_percent: float
    direction: TrendDirection
    is_anomaly: bool = False
    

@dataclass
class CampaignPerformance:
    """Campaign performance summary."""
    campaign_id: int
    campaign_name: str
    platform: str
    
    # Core metrics
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    spend: float = 0.0
    revenue: float = 0.0
    
    # Calculated metrics
    ctr: float = 0.0
    cvr: float = 0.0
    cpc: float = 0.0
    cpa: float = 0.0
    roas: float = 0.0
    
    # Trends
    trends: Dict[str, PerformanceTrend] = field(default_factory=dict)
    
    def calculate_metrics(self):
        """Calculate derived metrics."""
        self.ctr = (self.clicks / self.impressions * 100) if self.impressions > 0 else 0
        self.cvr = (self.conversions / self.clicks * 100) if self.clicks > 0 else 0
        self.cpc = (self.spend / self.clicks) if self.clicks > 0 else 0
        self.cpa = (self.spend / self.conversions) if self.conversions > 0 else 0
        self.roas = (self.revenue / self.spend) if self.spend > 0 else 0


class PerformanceTracker:
    """
    Tracks and analyzes campaign performance.
    """
    
    # Anomaly detection thresholds
    ANOMALY_THRESHOLDS = {
        "ctr": 30,      # 30% change is anomaly
        "cpc": 50,      # 50% change is anomaly
        "cvr": 40,      # 40% change is anomaly
        "spend": 100,   # 100% change is anomaly
    }
    
    def calculate_trend(
        self,
        current: float,
        previous: float,
        metric_name: str,
    ) -> PerformanceTrend:
        """Calculate trend for a metric."""
        if previous == 0:
            change = 100 if current > 0 else 0
        else:
            change = (current - previous) / previous * 100
        
        if abs(change) < 5:
            direction = TrendDirection.STABLE
        elif change > 0:
            direction = TrendDirection.UP
        else:
            direction = TrendDirection.DOWN
        
        threshold = self.ANOMALY_THRESHOLDS.get(metric_name, 50)
        is_anomaly = abs(change) > threshold
        
        return PerformanceTrend(
            metric_name=metric_name,
            current_value=current,
            previous_value=previous,
            change_percent=round(change, 2),
            direction=direction,
            is_anomaly=is_anomaly,
        )
    
    def analyze_campaign(
        self,
        current_metrics: Dict[str, float],
        previous_metrics: Dict[str, float],
        campaign_id: int,
        campaign_name: str,
        platform: str,
    ) -> CampaignPerformance:
        """Analyze campaign performance with trends."""
        perf = CampaignPerformance(
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            platform=platform,
            impressions=int(current_metrics.get("impressions", 0)),
            clicks=int(current_metrics.get("clicks", 0)),
            conversions=int(current_metrics.get("conversions", 0)),
            spend=current_metrics.get("spend", 0.0),
            revenue=current_metrics.get("revenue", 0.0),
        )
        
        perf.calculate_metrics()
        
        # Calculate trends
        for metric in ["ctr", "cvr", "cpc", "spend", "roas"]:
            current = getattr(perf, metric, 0)
            previous = previous_metrics.get(metric, 0)
            perf.trends[metric] = self.calculate_trend(current, previous, metric)
        
        return perf
    
    def get_performance_score(self, perf: CampaignPerformance) -> int:
        """
        Calculate overall performance score (0-100).
        """
        score = 50  # Baseline
        
        # ROAS impact (biggest weight)
        if perf.roas >= 3:
            score += 25
        elif perf.roas >= 2:
            score += 15
        elif perf.roas >= 1:
            score += 5
        else:
            score -= 15
        
        # CTR impact
        if perf.ctr >= 3:
            score += 10
        elif perf.ctr >= 1:
            score += 5
        else:
            score -= 5
        
        # CVR impact
        if perf.cvr >= 5:
            score += 10
        elif perf.cvr >= 2:
            score += 5
        
        # Trend bonuses
        for trend in perf.trends.values():
            if trend.direction == TrendDirection.UP and not trend.is_anomaly:
                score += 2
            elif trend.direction == TrendDirection.DOWN and trend.is_anomaly:
                score -= 5
        
        return max(0, min(100, score))
    
    def get_recommendations(self, perf: CampaignPerformance) -> List[str]:
        """Get optimization recommendations based on performance."""
        recommendations = []
        
        if perf.ctr < 1:
            recommendations.append("CTR низкий — попробуйте обновить заголовки объявлений")
        
        if perf.cvr < 2 and perf.clicks > 100:
            recommendations.append("CVR можно улучшить — проверьте посадочную страницу")
        
        if perf.cpc > 50:
            recommendations.append("CPC высокий — рассмотрите минус-слова или сужение таргетинга")
        
        if perf.roas < 1:
            recommendations.append("⚠️ ROAS меньше 1 — кампания убыточна, нужна оптимизация")
        elif perf.roas > 3:
            recommendations.append("🎯 Отличный ROAS! Можно увеличить бюджет")
        
        # Trend-based
        for metric, trend in perf.trends.items():
            if trend.is_anomaly and trend.direction == TrendDirection.DOWN:
                recommendations.append(f"⚠️ Резкое падение {metric} — проверьте кампанию")
        
        return recommendations


def format_performance_report(perf: CampaignPerformance, score: int) -> str:
    """Format performance as readable report."""
    lines = [
        f"📊 {perf.campaign_name} ({perf.platform})",
        f"",
        f"Показатели:",
        f"  • Показы: {perf.impressions:,}",
        f"  • Клики: {perf.clicks:,}",
        f"  • Конверсии: {perf.conversions:,}",
        f"  • Расход: {perf.spend:,.2f}₽",
        f"  • Доход: {perf.revenue:,.2f}₽",
        f"",
        f"Эффективность:",
        f"  • CTR: {perf.ctr:.2f}%",
        f"  • CVR: {perf.cvr:.2f}%",
        f"  • CPC: {perf.cpc:.2f}₽",
        f"  • ROAS: {perf.roas:.2f}x",
        f"",
        f"Оценка: {score}/100",
    ]
    
    return "\n".join(lines)
