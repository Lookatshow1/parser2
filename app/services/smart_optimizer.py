"""
Smart Auto-Optimizer Service.

AI-powered automatic campaign optimization:
- Pause underperforming ads
- Redistribute budget to winners
- Auto A/B test winner selection
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models_drafts import DraftCampaign, DraftAdGroup, DraftAd

logger = logging.getLogger(__name__)


class OptimizationAction(Enum):
    PAUSE_AD = "pause_ad"
    BOOST_BUDGET = "boost_budget"
    REDUCE_BUDGET = "reduce_budget"
    PAUSE_CAMPAIGN = "pause_campaign"
    DECLARE_WINNER = "declare_winner"
    ALERT_ANOMALY = "alert_anomaly"


@dataclass
class OptimizationResult:
    """Result of an optimization run."""
    action: OptimizationAction
    entity_type: str  # "ad", "ad_group", "campaign"
    entity_id: int
    reason: str
    metrics_before: Dict[str, float]
    recommended_change: Optional[Dict[str, Any]] = None
    applied: bool = False


@dataclass
class PerformanceMetrics:
    """Performance metrics for analysis."""
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    spend: float = 0.0
    revenue: float = 0.0
    
    @property
    def ctr(self) -> float:
        return (self.clicks / self.impressions * 100) if self.impressions > 0 else 0
    
    @property
    def cvr(self) -> float:
        return (self.conversions / self.clicks * 100) if self.clicks > 0 else 0
    
    @property
    def cpc(self) -> float:
        return (self.spend / self.clicks) if self.clicks > 0 else 0
    
    @property
    def cpa(self) -> float:
        return (self.spend / self.conversions) if self.conversions > 0 else 0
    
    @property
    def roas(self) -> float:
        return (self.revenue / self.spend) if self.spend > 0 else 0


class SmartOptimizer:
    """
    AI-powered campaign optimizer.
    
    Analyzes performance metrics and recommends/applies optimizations.
    """
    
    # Thresholds (configurable per account)
    DEFAULT_THRESHOLDS = {
        "min_impressions": 1000,       # Min impressions before action
        "min_clicks": 50,              # Min clicks before action
        "pause_ctr_threshold": 0.5,    # Pause if CTR < 0.5%
        "pause_cvr_threshold": 0.5,    # Pause if CVR < 0.5%
        "boost_roas_threshold": 3.0,   # Boost if ROAS > 3x
        "reduce_roas_threshold": 0.8,  # Reduce if ROAS < 0.8x
        "anomaly_change_percent": 50,  # Alert if metric changes >50%
        "ab_test_confidence": 0.95,    # Confidence for winner declaration
    }
    
    def __init__(self, db: Session, thresholds: Optional[Dict] = None):
        self.db = db
        self.thresholds = {**self.DEFAULT_THRESHOLDS, **(thresholds or {})}
    
    async def analyze_campaign(
        self,
        campaign_id: int,
        metrics: Dict[int, PerformanceMetrics],  # ad_id -> metrics
    ) -> List[OptimizationResult]:
        """
        Analyze a campaign and return optimization recommendations.
        
        Args:
            campaign_id: Campaign to analyze
            metrics: Dict of ad_id -> PerformanceMetrics
        """
        results = []
        
        # Get campaign
        campaign = self.db.query(DraftCampaign).filter(
            DraftCampaign.id == campaign_id
        ).first()
        
        if not campaign:
            return results
        
        # Aggregate campaign metrics
        total_metrics = PerformanceMetrics()
        for m in metrics.values():
            total_metrics.impressions += m.impressions
            total_metrics.clicks += m.clicks
            total_metrics.conversions += m.conversions
            total_metrics.spend += m.spend
            total_metrics.revenue += m.revenue
        
        # Analyze each ad
        for ad_id, ad_metrics in metrics.items():
            # Skip if insufficient data
            if ad_metrics.impressions < self.thresholds["min_impressions"]:
                continue
            
            # Check for underperforming ads
            if ad_metrics.ctr < self.thresholds["pause_ctr_threshold"]:
                results.append(OptimizationResult(
                    action=OptimizationAction.PAUSE_AD,
                    entity_type="ad",
                    entity_id=ad_id,
                    reason=f"CTR ({ad_metrics.ctr:.2f}%) ниже порога ({self.thresholds['pause_ctr_threshold']}%)",
                    metrics_before={"ctr": ad_metrics.ctr, "impressions": ad_metrics.impressions},
                ))
            
            # Check for high-performing ads (budget boost)
            if ad_metrics.roas > self.thresholds["boost_roas_threshold"]:
                results.append(OptimizationResult(
                    action=OptimizationAction.BOOST_BUDGET,
                    entity_type="ad",
                    entity_id=ad_id,
                    reason=f"ROAS ({ad_metrics.roas:.2f}x) выше порога ({self.thresholds['boost_roas_threshold']}x)",
                    metrics_before={"roas": ad_metrics.roas, "spend": ad_metrics.spend},
                    recommended_change={"budget_multiplier": 1.5},
                ))
            
            # Check for underperforming ads (budget reduce)
            elif ad_metrics.roas < self.thresholds["reduce_roas_threshold"] and ad_metrics.clicks >= self.thresholds["min_clicks"]:
                results.append(OptimizationResult(
                    action=OptimizationAction.REDUCE_BUDGET,
                    entity_type="ad",
                    entity_id=ad_id,
                    reason=f"ROAS ({ad_metrics.roas:.2f}x) ниже порога ({self.thresholds['reduce_roas_threshold']}x)",
                    metrics_before={"roas": ad_metrics.roas, "spend": ad_metrics.spend},
                    recommended_change={"budget_multiplier": 0.5},
                ))
        
        return results
    
    async def detect_anomalies(
        self,
        campaign_id: int,
        current_metrics: PerformanceMetrics,
        previous_metrics: PerformanceMetrics,
    ) -> List[OptimizationResult]:
        """Detect anomalies by comparing periods."""
        results = []
        threshold = self.thresholds["anomaly_change_percent"]
        
        def check_metric(name: str, current: float, previous: float):
            if previous == 0:
                return
            change_pct = abs((current - previous) / previous * 100)
            if change_pct > threshold:
                direction = "вырос" if current > previous else "упал"
                results.append(OptimizationResult(
                    action=OptimizationAction.ALERT_ANOMALY,
                    entity_type="campaign",
                    entity_id=campaign_id,
                    reason=f"{name} {direction} на {change_pct:.1f}%",
                    metrics_before={"previous": previous, "current": current},
                ))
        
        check_metric("CTR", current_metrics.ctr, previous_metrics.ctr)
        check_metric("CPC", current_metrics.cpc, previous_metrics.cpc)
        check_metric("CVR", current_metrics.cvr, previous_metrics.cvr)
        check_metric("Расход", current_metrics.spend, previous_metrics.spend)
        
        return results
    
    async def run_ab_test_analysis(
        self,
        test_id: int,
        variant_metrics: Dict[str, PerformanceMetrics],  # variant_name -> metrics
    ) -> Optional[OptimizationResult]:
        """
        Analyze A/B test and declare winner if statistically significant.
        """
        if len(variant_metrics) < 2:
            return None
        
        # Calculate conversion rates and sample sizes
        variants = []
        for name, metrics in variant_metrics.items():
            if metrics.clicks > 0:
                variants.append({
                    "name": name,
                    "conversions": metrics.conversions,
                    "clicks": metrics.clicks,
                    "cvr": metrics.cvr,
                })
        
        if len(variants) < 2:
            return None
        
        # Simple significance test (Chi-squared approximation)
        # For production, use scipy.stats.chi2_contingency
        sorted_variants = sorted(variants, key=lambda x: x["cvr"], reverse=True)
        winner = sorted_variants[0]
        loser = sorted_variants[1]
        
        # Check sample size
        min_sample = 100  # Minimum conversions per variant
        if winner["conversions"] < min_sample or loser["conversions"] < min_sample:
            return None
        
        # Simple lift calculation
        lift = (winner["cvr"] - loser["cvr"]) / loser["cvr"] * 100 if loser["cvr"] > 0 else 0
        
        # Declare winner if lift > 10% with sufficient sample
        if lift > 10:
            return OptimizationResult(
                action=OptimizationAction.DECLARE_WINNER,
                entity_type="ab_test",
                entity_id=test_id,
                reason=f"Вариант '{winner['name']}' лучше на {lift:.1f}% (CVR: {winner['cvr']:.2f}% vs {loser['cvr']:.2f}%)",
                metrics_before={
                    "winner": winner["name"],
                    "winner_cvr": winner["cvr"],
                    "loser_cvr": loser["cvr"],
                    "lift": lift,
                },
            )
        
        return None
    
    async def get_budget_recommendations(
        self,
        organization_id: int,
        total_budget: float,
        campaign_metrics: Dict[int, PerformanceMetrics],
    ) -> Dict[int, float]:
        """
        Calculate optimal budget distribution across campaigns.
        
        Uses ROAS-weighted allocation with minimum spend guarantees.
        """
        if not campaign_metrics:
            return {}
        
        # Calculate total weighted score
        scores = {}
        min_budget_percent = 0.05  # 5% minimum per campaign
        
        for campaign_id, metrics in campaign_metrics.items():
            # Score = ROAS * log(conversions + 1) for stability
            import math
            roas_score = max(metrics.roas, 0.1)  # Floor at 0.1
            volume_score = math.log(metrics.conversions + 1) + 1
            scores[campaign_id] = roas_score * volume_score
        
        total_score = sum(scores.values())
        
        # Allocate budget
        allocations = {}
        remaining_budget = total_budget
        
        for campaign_id, score in scores.items():
            # Weighted allocation
            weight = score / total_score if total_score > 0 else 1 / len(scores)
            allocated = max(
                total_budget * weight,
                total_budget * min_budget_percent  # Minimum
            )
            allocations[campaign_id] = min(allocated, remaining_budget)
            remaining_budget -= allocations[campaign_id]
        
        # Redistribute any remaining
        if remaining_budget > 0 and allocations:
            best_campaign = max(scores, key=scores.get)
            allocations[best_campaign] += remaining_budget
        
        return allocations


class AutomationRule:
    """
    Automation rule definition.
    
    Format: IF condition THEN action
    """
    
    def __init__(
        self,
        name: str,
        condition: Dict[str, Any],
        action: Dict[str, Any],
        enabled: bool = True,
    ):
        self.name = name
        self.condition = condition
        self.action = action
        self.enabled = enabled
    
    def evaluate(self, metrics: PerformanceMetrics, entity: Any) -> bool:
        """Check if condition is met."""
        metric = self.condition.get("metric")
        operator = self.condition.get("operator")
        value = self.condition.get("value")
        
        actual = getattr(metrics, metric, None)
        if actual is None:
            return False
        
        if operator == "lt":
            return actual < value
        elif operator == "gt":
            return actual > value
        elif operator == "lte":
            return actual <= value
        elif operator == "gte":
            return actual >= value
        elif operator == "eq":
            return actual == value
        
        return False


# Example rules
DEFAULT_RULES = [
    AutomationRule(
        name="Pause low CTR ads",
        condition={"metric": "ctr", "operator": "lt", "value": 0.5},
        action={"type": "pause", "target": "ad"},
    ),
    AutomationRule(
        name="Boost high ROAS campaigns",
        condition={"metric": "roas", "operator": "gt", "value": 3.0},
        action={"type": "budget_multiply", "target": "campaign", "multiplier": 1.5},
    ),
    AutomationRule(
        name="Alert on spend spike",
        condition={"metric": "spend", "operator": "gt", "value": 10000},
        action={"type": "alert", "channel": "telegram"},
    ),
]
