"""
Auto-Optimization Service.

Automated bid management and campaign optimization based on performance data.
"""
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# =============================================================================
# DATA TYPES
# =============================================================================

class OptimizationAction(str, Enum):
    """Types of optimization actions."""
    INCREASE_BID = "increase_bid"
    DECREASE_BID = "decrease_bid"
    PAUSE_AD = "pause_ad"
    ENABLE_AD = "enable_ad"
    PAUSE_KEYWORD = "pause_keyword"
    INCREASE_BUDGET = "increase_budget"
    DECREASE_BUDGET = "decrease_budget"


class Priority(str, Enum):
    """Recommendation priority."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class OptimizationRecommendation:
    """A single optimization recommendation."""
    id: str
    action: OptimizationAction
    priority: Priority
    title: str
    description: str
    expected_impact: str
    
    # Context
    campaign_id: Optional[int] = None
    ad_id: Optional[int] = None
    keyword_id: Optional[int] = None
    
    # Values
    current_value: Optional[str] = None
    suggested_value: Optional[str] = None
    
    # Metadata
    created_at: datetime = None
    expires_at: datetime = None


@dataclass
class OptimizationRule:
    """Rule for automated optimization."""
    id: str
    name: str
    condition: str  # e.g., "CTR < 1.0"
    action: OptimizationAction
    value: str  # e.g., "-10%" or "pause"
    enabled: bool = True


# =============================================================================
# AUTO-OPTIMIZATION SERVICE
# =============================================================================

class AutoOptimizationService:
    """
    Service for automated campaign optimization.
    
    Analyzes performance metrics and generates recommendations
    or applies automatic optimizations based on rules.
    """
    
    # Default thresholds
    CTR_LOW_THRESHOLD = 1.0  # %
    CTR_DROP_THRESHOLD = 0.3  # 30% drop
    CPA_HIGH_MULTIPLIER = 1.5  # 150% of target CPA
    ROAS_LOW_THRESHOLD = 1.0  # Break-even
    BUDGET_LOW_THRESHOLD = 0.15  # 15% remaining
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_campaign(
        self, 
        campaign_id: int,
        metrics: Dict[str, Any],
        target_cpa: Optional[float] = None,
        target_roas: Optional[float] = None,
    ) -> List[OptimizationRecommendation]:
        """
        Analyze campaign performance and generate recommendations.
        
        Args:
            campaign_id: Campaign ID
            metrics: Current metrics (ctr, cpc, conversions, spend, etc.)
            target_cpa: Target cost per acquisition
            target_roas: Target return on ad spend
            
        Returns:
            List of optimization recommendations
        """
        recommendations = []
        now = datetime.utcnow()
        
        ctr = metrics.get("ctr", 0)
        cpc = metrics.get("cpc", 0)
        conversions = metrics.get("conversions", 0)
        spend = metrics.get("spend", 0)
        budget = metrics.get("budget", 0)
        impressions = metrics.get("impressions", 0)
        clicks = metrics.get("clicks", 0)
        
        # Calculate derived metrics
        actual_cpa = spend / conversions if conversions > 0 else 0
        budget_remaining = (budget - spend) / budget if budget > 0 else 0
        
        # 1. Low CTR check
        if ctr < self.CTR_LOW_THRESHOLD and impressions > 1000:
            recommendations.append(OptimizationRecommendation(
                id=f"ctr_low_{campaign_id}_{now.timestamp()}",
                action=OptimizationAction.PAUSE_AD,
                priority=Priority.MEDIUM,
                title="Низкий CTR — рассмотрите изменение объявления",
                description=f"CTR {ctr:.2f}% ниже порога {self.CTR_LOW_THRESHOLD}%",
                expected_impact="Экономия бюджета",
                campaign_id=campaign_id,
                current_value=f"{ctr:.2f}%",
                suggested_value=f">{self.CTR_LOW_THRESHOLD}%",
                created_at=now,
                expires_at=now + timedelta(days=3),
            ))
        
        # 2. High CPA check
        if target_cpa and actual_cpa > target_cpa * self.CPA_HIGH_MULTIPLIER:
            recommendations.append(OptimizationRecommendation(
                id=f"cpa_high_{campaign_id}_{now.timestamp()}",
                action=OptimizationAction.DECREASE_BID,
                priority=Priority.HIGH,
                title="CPA выше целевого — снизьте ставки",
                description=f"CPA ₽{actual_cpa:.0f} превышает цель ₽{target_cpa:.0f} на {((actual_cpa/target_cpa)-1)*100:.0f}%",
                expected_impact=f"Снижение CPA до ₽{target_cpa:.0f}",
                campaign_id=campaign_id,
                current_value=f"₽{actual_cpa:.0f}",
                suggested_value=f"₽{target_cpa:.0f}",
                created_at=now,
                expires_at=now + timedelta(days=1),
            ))
        
        # 3. Budget running low
        if budget_remaining < self.BUDGET_LOW_THRESHOLD and budget > 0:
            recommendations.append(OptimizationRecommendation(
                id=f"budget_low_{campaign_id}_{now.timestamp()}",
                action=OptimizationAction.INCREASE_BUDGET,
                priority=Priority.HIGH,
                title="Бюджет заканчивается",
                description=f"Осталось {budget_remaining*100:.1f}% бюджета",
                expected_impact="Продолжение показов",
                campaign_id=campaign_id,
                current_value=f"₽{budget-spend:.0f}",
                suggested_value=f"Пополнить",
                created_at=now,
                expires_at=now + timedelta(hours=12),
            ))
        
        # 4. Good performance - scale up
        if target_cpa and actual_cpa < target_cpa * 0.7 and conversions >= 5:
            recommendations.append(OptimizationRecommendation(
                id=f"scale_up_{campaign_id}_{now.timestamp()}",
                action=OptimizationAction.INCREASE_BID,
                priority=Priority.MEDIUM,
                title="Отличные результаты — масштабируйте",
                description=f"CPA ₽{actual_cpa:.0f} на 30% ниже цели — есть потенциал для роста",
                expected_impact="+30% конверсий",
                campaign_id=campaign_id,
                current_value=f"₽{actual_cpa:.0f}",
                suggested_value=f"Увеличить ставку на 20%",
                created_at=now,
                expires_at=now + timedelta(days=3),
            ))
        
        return recommendations
    
    def apply_rule(
        self,
        rule: OptimizationRule,
        campaign_id: int,
        current_metrics: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Check if rule applies and return action to execute.
        
        Returns:
            Action dict if rule applies, None otherwise.
        """
        if not rule.enabled:
            return None
        
        # Parse condition (simple format: "metric operator value")
        # Examples: "CTR < 1.0", "CPA > 500", "ROAS < 1.5"
        try:
            parts = rule.condition.split()
            metric = parts[0].lower()
            operator = parts[1]
            threshold = float(parts[2])
            
            current_value = current_metrics.get(metric, 0)
            
            condition_met = False
            if operator == "<":
                condition_met = current_value < threshold
            elif operator == ">":
                condition_met = current_value > threshold
            elif operator == "<=":
                condition_met = current_value <= threshold
            elif operator == ">=":
                condition_met = current_value >= threshold
            
            if condition_met:
                return {
                    "rule_id": rule.id,
                    "campaign_id": campaign_id,
                    "action": rule.action,
                    "value": rule.value,
                    "reason": f"{rule.condition} triggered ({metric}={current_value})",
                }
                
        except Exception as e:
            logger.warning(f"Failed to parse rule {rule.id}: {e}")
        
        return None
    
    def get_default_rules(self) -> List[OptimizationRule]:
        """Get default optimization rules."""
        return [
            OptimizationRule(
                id="pause_low_ctr",
                name="Приостановить при низком CTR",
                condition="ctr < 0.5",
                action=OptimizationAction.PAUSE_AD,
                value="pause",
            ),
            OptimizationRule(
                id="decrease_high_cpc",
                name="Снизить ставку при высоком CPC",
                condition="cpc > 100",
                action=OptimizationAction.DECREASE_BID,
                value="-15%",
            ),
            OptimizationRule(
                id="increase_good_roas",
                name="Увеличить ставку при хорошем ROAS",
                condition="roas > 3.0",
                action=OptimizationAction.INCREASE_BID,
                value="+20%",
            ),
        ]


# =============================================================================
# FACTORY
# =============================================================================

def get_auto_optimization_service(db: Session) -> AutoOptimizationService:
    """Get auto-optimization service instance."""
    return AutoOptimizationService(db)
