"""
A/B Testing Service

Business logic for managing A/B tests and calculating statistical significance.
"""
import math
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db.models_abtests import ABTest, ABTestVariant, ABTestResult, ABTestStatus


def chi2_contingency_simple(observed):
    """
    Simple Chi-squared test for 2x2 contingency table.
    Returns chi2 statistic and p-value.
    """
    # observed = [[clicks_a, non_clicks_a], [clicks_b, non_clicks_b]]
    a, b = observed[0]
    c, d = observed[1]
    
    n = a + b + c + d
    if n == 0:
        return 0.0, 1.0
    
    # Expected values
    row1 = a + b
    row2 = c + d
    col1 = a + c
    col2 = b + d
    
    expected = [
        [row1 * col1 / n, row1 * col2 / n],
        [row2 * col1 / n, row2 * col2 / n]
    ]
    
    # Chi-squared statistic
    chi2 = 0.0
    for i in range(2):
        for j in range(2):
            e = expected[i][j]
            if e > 0:
                chi2 += (observed[i][j] - e) ** 2 / e
    
    # Approximate p-value using chi2 distribution (1 degree of freedom)
    # Simple approximation for p-value
    if chi2 < 3.84:
        p_value = 1.0 - chi2 / 10  # rough approximation
    elif chi2 < 6.63:
        p_value = 0.05  # ~ 95% confidence
    elif chi2 < 10.83:
        p_value = 0.01  # ~ 99% confidence
    else:
        p_value = 0.001  # ~ 99.9% confidence
    
    return chi2, max(0.001, min(1.0, p_value))



class ABTestService:
    """Service for managing A/B tests."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_test(
        self,
        organization_id: int,
        name: str,
        variants: List[Dict[str, Any]],
        description: str = None,
        primary_metric: str = "ctr",
        min_sample_size: int = 1000,
        confidence_level: float = 0.95
    ) -> ABTest:
        """Create a new A/B test with variants."""
        
        # Calculate traffic split
        num_variants = len(variants)
        traffic_per_variant = 100 // num_variants
        
        test = ABTest(
            organization_id=organization_id,
            name=name,
            description=description,
            status=ABTestStatus.DRAFT.value,
            primary_metric=primary_metric,
            min_sample_size=min_sample_size,
            confidence_level=confidence_level,
            traffic_split={f"variant_{i}": traffic_per_variant for i in range(num_variants)}
        )
        self.session.add(test)
        await self.session.flush()
        
        # Create variants
        for i, v in enumerate(variants):
            variant = ABTestVariant(
                ab_test_id=test.id,
                name=v.get("name", f"Вариант {chr(65 + i)}"),  # A, B, C...
                title=v.get("title"),
                text=v.get("text"),
                landing_url=v.get("landing_url"),
                draft_ad_id=v.get("draft_ad_id"),
                traffic_percentage=traffic_per_variant
            )
            self.session.add(variant)
        
        await self.session.commit()
        await self.session.refresh(test)
        return test
    
    async def start_test(self, test_id: int) -> ABTest:
        """Start running an A/B test."""
        result = await self.session.execute(
            select(ABTest).where(ABTest.id == test_id)
        )
        test = result.scalar_one_or_none()
        
        if not test:
            raise ValueError("Тест не найден")
        
        test.status = ABTestStatus.RUNNING.value
        test.started_at = datetime.utcnow()
        await self.session.commit()
        return test
    
    async def pause_test(self, test_id: int) -> ABTest:
        """Pause a running A/B test."""
        result = await self.session.execute(
            select(ABTest).where(ABTest.id == test_id)
        )
        test = result.scalar_one_or_none()
        
        if not test:
            raise ValueError("Тест не найден")
        
        test.status = ABTestStatus.PAUSED.value
        await self.session.commit()
        return test
    
    async def update_metrics(self, variant_id: int, metrics: Dict[str, Any]) -> ABTestVariant:
        """Update metrics for a variant (called by sync jobs)."""
        result = await self.session.execute(
            select(ABTestVariant).where(ABTestVariant.id == variant_id)
        )
        variant = result.scalar_one_or_none()
        
        if not variant:
            raise ValueError("Вариант не найден")
        
        # Update cumulative metrics
        variant.impressions += metrics.get("impressions", 0)
        variant.clicks += metrics.get("clicks", 0)
        variant.conversions += metrics.get("conversions", 0)
        variant.spend += metrics.get("spend", 0.0)
        variant.revenue += metrics.get("revenue", 0.0)
        
        # Recalculate derived metrics
        if variant.impressions > 0:
            variant.ctr = (variant.clicks / variant.impressions) * 100
        if variant.clicks > 0:
            variant.conversion_rate = (variant.conversions / variant.clicks) * 100
            variant.cpc = variant.spend / variant.clicks
        if variant.spend > 0:
            variant.roas = variant.revenue / variant.spend
        
        variant.updated_at = datetime.utcnow()
        await self.session.commit()
        return variant
    
    async def calculate_significance(self, test_id: int) -> Dict[str, Any]:
        """
        Calculate statistical significance between variants.
        Uses Chi-squared test for proportions (CTR comparison).
        """
        result = await self.session.execute(
            select(ABTestVariant).where(ABTestVariant.ab_test_id == test_id)
        )
        variants = result.scalars().all()
        
        if len(variants) < 2:
            return {"significant": False, "reason": "Недостаточно вариантов"}
        
        # Get the two main variants
        variant_a = variants[0]
        variant_b = variants[1]
        
        # Check minimum sample size
        total_impressions = variant_a.impressions + variant_b.impressions
        if total_impressions < 100:
            return {
                "significant": False,
                "reason": "Недостаточно данных",
                "current_sample": total_impressions,
                "required_sample": 100
            }
        
        # Chi-squared test for CTR comparison
        # Observed: [[clicks_a, non_clicks_a], [clicks_b, non_clicks_b]]
        observed = [
            [variant_a.clicks, variant_a.impressions - variant_a.clicks],
            [variant_b.clicks, variant_b.impressions - variant_b.clicks]
        ]
        
        try:
            chi2, p_value = chi2_contingency_simple(observed)
        except Exception:
            return {"significant": False, "reason": "Ошибка расчёта"}

        
        # Get the test's confidence level
        test_result = await self.session.execute(
            select(ABTest).where(ABTest.id == test_id)
        )
        test = test_result.scalar_one_or_none()
        alpha = 1 - (test.confidence_level if test else 0.95)
        
        significant = p_value < alpha
        
        # Determine winner
        winner = None
        if significant:
            winner = variant_a if variant_a.ctr > variant_b.ctr else variant_b
        
        return {
            "significant": significant,
            "p_value": round(p_value, 4),
            "chi2": round(chi2, 2),
            "confidence": round((1 - p_value) * 100, 1),
            "winner_id": winner.id if winner else None,
            "winner_name": winner.name if winner else None,
            "variant_a": {
                "id": variant_a.id,
                "name": variant_a.name,
                "ctr": round(variant_a.ctr, 2),
                "impressions": variant_a.impressions,
                "clicks": variant_a.clicks
            },
            "variant_b": {
                "id": variant_b.id,
                "name": variant_b.name,
                "ctr": round(variant_b.ctr, 2),
                "impressions": variant_b.impressions,
                "clicks": variant_b.clicks
            }
        }
    
    async def select_winner(self, test_id: int, variant_id: int) -> ABTest:
        """Manually select a winner and complete the test."""
        result = await self.session.execute(
            select(ABTest).where(ABTest.id == test_id)
        )
        test = result.scalar_one_or_none()
        
        if not test:
            raise ValueError("Тест не найден")
        
        # Get significance data
        sig_data = await self.calculate_significance(test_id)
        
        test.winner_variant_id = variant_id
        test.statistical_significance = sig_data.get("p_value")
        test.status = ABTestStatus.WINNER_SELECTED.value
        test.ended_at = datetime.utcnow()
        
        await self.session.commit()
        return test
    
    async def auto_select_winner(self, test_id: int) -> Optional[ABTest]:
        """Automatically select winner if statistically significant."""
        sig_data = await self.calculate_significance(test_id)
        
        if sig_data.get("significant") and sig_data.get("winner_id"):
            return await self.select_winner(test_id, sig_data["winner_id"])
        
        return None
    
    async def list_tests(self, organization_id: int, status: str = None) -> List[ABTest]:
        """List all A/B tests for an organization."""
        query = select(ABTest).where(ABTest.organization_id == organization_id)
        
        if status:
            query = query.where(ABTest.status == status)
        
        query = query.order_by(ABTest.created_at.desc())
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_test(self, test_id: int) -> Optional[ABTest]:
        """Get a single A/B test with variants."""
        result = await self.session.execute(
            select(ABTest).where(ABTest.id == test_id)
        )
        return result.scalar_one_or_none()
