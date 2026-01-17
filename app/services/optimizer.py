"""
Budget Optimizer Service

AI-powered budget allocation and optimization rules engine.
"""
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db.models_optimizer import BudgetAllocation, OptimizationRule, OptimizationLog
from app.db.models_analytics import CampaignMetrics


class BudgetOptimizerService:
    """Service for AI-powered budget optimization."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def generate_recommendations(
        self,
        organization_id: int,
        total_budget: float = None
    ) -> List[BudgetAllocation]:
        """
        Generate budget allocation recommendations based on performance.
        Uses ROAS-based optimization strategy.
        """
        # Get recent metrics by platform
        date_from = date.today() - timedelta(days=7)
        
        query = select(CampaignMetrics).where(
            and_(
                CampaignMetrics.organization_id == organization_id,
                CampaignMetrics.date >= date_from
            )
        )
        
        result = await self.session.execute(query)
        metrics = result.scalars().all()
        
        if not metrics:
            # Generate mock recommendations for demo
            return await self._generate_mock_recommendations(organization_id)
        
        # Aggregate by platform
        platform_data = {}
        for m in metrics:
            if m.platform not in platform_data:
                platform_data[m.platform] = {"spend": 0, "revenue": 0}
            platform_data[m.platform]["spend"] += m.spend or 0
            platform_data[m.platform]["revenue"] += m.revenue or 0
        
        # Calculate ROAS and generate recommendations
        recommendations = []
        total_roas = sum(
            d["revenue"] / d["spend"] if d["spend"] > 0 else 0 
            for d in platform_data.values()
        )
        
        for platform, data in platform_data.items():
            current_roas = data["revenue"] / data["spend"] if data["spend"] > 0 else 0
            avg_roas = total_roas / len(platform_data) if platform_data else 0
            
            # Calculate recommended change
            if current_roas > avg_roas * 1.2:  # 20% above average
                change_pct = 15  # Increase by 15%
                reason = f"ROAS выше среднего ({current_roas:.2f}x vs {avg_roas:.2f}x)"
            elif current_roas < avg_roas * 0.8:  # 20% below average
                change_pct = -15  # Decrease by 15%
                reason = f"ROAS ниже среднего ({current_roas:.2f}x vs {avg_roas:.2f}x)"
            else:
                change_pct = 0
                reason = "ROAS в пределах нормы"
            
            current_budget = data["spend"] / 7  # Daily budget
            recommended_budget = current_budget * (1 + change_pct / 100)
            
            allocation = BudgetAllocation(
                organization_id=organization_id,
                platform=platform,
                current_budget=round(current_budget, 2),
                recommended_budget=round(recommended_budget, 2),
                change_percentage=change_pct,
                reason=reason,
                expected_roas_improvement=5.0 if change_pct > 0 else 0,
                status="pending"
            )
            self.session.add(allocation)
            recommendations.append(allocation)
        
        await self.session.commit()
        return recommendations
    
    async def _generate_mock_recommendations(self, organization_id: int) -> List[BudgetAllocation]:
        """Generate mock recommendations for demo purposes."""
        mock_data = [
            {
                "platform": "yandex",
                "current_budget": 15000,
                "recommended_budget": 17250,
                "change_percentage": 15,
                "reason": "ROAS 4.8x — эффективнее других платформ",
                "expected_roas_improvement": 8.5
            },
            {
                "platform": "google",
                "current_budget": 12000,
                "recommended_budget": 12000,
                "change_percentage": 0,
                "reason": "ROAS 4.2x — в пределах нормы",
                "expected_roas_improvement": 0
            },
            {
                "platform": "vk",
                "current_budget": 8000,
                "recommended_budget": 6800,
                "change_percentage": -15,
                "reason": "ROAS 2.9x — ниже среднего, рекомендуем снизить",
                "expected_roas_improvement": 0
            }
        ]
        
        recommendations = []
        for data in mock_data:
            allocation = BudgetAllocation(
                organization_id=organization_id,
                platform=data["platform"],
                current_budget=data["current_budget"],
                recommended_budget=data["recommended_budget"],
                change_percentage=data["change_percentage"],
                reason=data["reason"],
                expected_roas_improvement=data["expected_roas_improvement"],
                status="pending"
            )
            self.session.add(allocation)
            recommendations.append(allocation)
        
        await self.session.commit()
        return recommendations
    
    async def apply_recommendation(self, allocation_id: int) -> BudgetAllocation:
        """Apply a budget recommendation."""
        result = await self.session.execute(
            select(BudgetAllocation).where(BudgetAllocation.id == allocation_id)
        )
        allocation = result.scalar_one_or_none()
        
        if not allocation:
            raise ValueError("Рекомендация не найдена")
        
        # Log the action
        log = OptimizationLog(
            organization_id=allocation.organization_id,
            action_type="budget_change",
            description=f"Применено изменение бюджета для {allocation.platform}",
            platform=allocation.platform,
            before_value=allocation.current_budget,
            after_value=allocation.recommended_budget,
            status="executed"
        )
        self.session.add(log)
        
        allocation.status = "applied"
        allocation.applied_at = datetime.utcnow()
        
        await self.session.commit()
        return allocation
    
    async def reject_recommendation(self, allocation_id: int) -> BudgetAllocation:
        """Reject a budget recommendation."""
        result = await self.session.execute(
            select(BudgetAllocation).where(BudgetAllocation.id == allocation_id)
        )
        allocation = result.scalar_one_or_none()
        
        if not allocation:
            raise ValueError("Рекомендация не найдена")
        
        allocation.status = "rejected"
        await self.session.commit()
        return allocation
    
    async def create_rule(
        self,
        organization_id: int,
        name: str,
        rule_type: str,
        conditions: Dict[str, Any],
        actions: Dict[str, Any],
        description: str = None,
        platform: str = None
    ) -> OptimizationRule:
        """Create an automation rule."""
        rule = OptimizationRule(
            organization_id=organization_id,
            name=name,
            description=description,
            rule_type=rule_type,
            conditions=conditions,
            actions=actions,
            platform=platform,
            is_enabled=True
        )
        self.session.add(rule)
        await self.session.commit()
        return rule
    
    async def list_rules(self, organization_id: int) -> List[OptimizationRule]:
        """List all automation rules."""
        result = await self.session.execute(
            select(OptimizationRule)
            .where(OptimizationRule.organization_id == organization_id)
            .order_by(OptimizationRule.created_at.desc())
        )
        return result.scalars().all()
    
    async def toggle_rule(self, rule_id: int, enabled: bool) -> OptimizationRule:
        """Enable or disable a rule."""
        result = await self.session.execute(
            select(OptimizationRule).where(OptimizationRule.id == rule_id)
        )
        rule = result.scalar_one_or_none()
        
        if not rule:
            raise ValueError("Правило не найдено")
        
        rule.is_enabled = enabled
        await self.session.commit()
        return rule
    
    async def get_pending_recommendations(self, organization_id: int) -> List[BudgetAllocation]:
        """Get all pending recommendations."""
        result = await self.session.execute(
            select(BudgetAllocation)
            .where(
                and_(
                    BudgetAllocation.organization_id == organization_id,
                    BudgetAllocation.status == "pending"
                )
            )
            .order_by(BudgetAllocation.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_optimization_history(self, organization_id: int, limit: int = 50) -> List[OptimizationLog]:
        """Get optimization action history."""
        result = await self.session.execute(
            select(OptimizationLog)
            .where(OptimizationLog.organization_id == organization_id)
            .order_by(OptimizationLog.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
