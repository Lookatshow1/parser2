"""
Optimization API Endpoints.

Smart auto-optimization, competitor analysis, creative studio, cascade generation APIs.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

import logging

from app.api.deps import get_db, get_current_user, get_current_org
from app.db.models import User, Organization
from app.services.smart_optimizer import SmartOptimizer, PerformanceMetrics
from app.services.competitor_intelligence import CompetitorIntelligence
from app.services.creative_studio import CreativeStudio
from app.services.cascade_pipeline import CascadeImagePipeline
from app.services.utm_builder import UTMBuilder
from app.services.rag_service import RagService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI"])


# =============================================================================
# SCHEMAS
# =============================================================================

class OptimizationRequest(BaseModel):
    campaign_id: int
    metrics: Dict[int, Dict[str, float]]  # ad_id -> {impressions, clicks, ...}


class OptimizationResponse(BaseModel):
    actions: List[Dict[str, Any]]
    summary: str


class CompetitorRequest(BaseModel):
    domain: str


class CompetitorCompareRequest(BaseModel):
    my_domain: str
    competitor_domain: str


class VariationsRequest(BaseModel):
    title: str
    text: str
    count: int = 50
    platform: str = "yandex"
    business_context: Optional[str] = None


class PredictRequest(BaseModel):
    title: str
    text: str
    industry: str
    target_audience: Optional[str] = None


class ABTestSuggestRequest(BaseModel):
    title: str
    text: str


# =============================================================================
# OPTIMIZATION ENDPOINTS
# =============================================================================

@router.post("/optimize", response_model=OptimizationResponse)
async def optimize_campaign(
    payload: OptimizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run AI optimization analysis on a campaign."""
    optimizer = SmartOptimizer(db)
    
    # Convert metrics to PerformanceMetrics objects
    metrics = {}
    for ad_id, m in payload.metrics.items():
        metrics[int(ad_id)] = PerformanceMetrics(
            impressions=m.get("impressions", 0),
            clicks=m.get("clicks", 0),
            conversions=m.get("conversions", 0),
            spend=m.get("spend", 0.0),
            revenue=m.get("revenue", 0.0),
        )
    
    results = await optimizer.analyze_campaign(payload.campaign_id, metrics)
    
    actions = [
        {
            "action": r.action.value,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "reason": r.reason,
            "metrics": r.metrics_before,
            "recommended_change": r.recommended_change,
        }
        for r in results
    ]
    
    summary = f"Найдено {len(actions)} оптимизаций"
    if actions:
        pause_count = sum(1 for a in actions if a["action"] == "pause_ad")
        boost_count = sum(1 for a in actions if a["action"] == "boost_budget")
        if pause_count:
            summary += f", {pause_count} объявлений к паузе"
        if boost_count:
            summary += f", {boost_count} к буста бюджета"
    
    return OptimizationResponse(actions=actions, summary=summary)


@router.post("/budget-allocation")
async def get_budget_allocation(
    total_budget: float,
    campaign_metrics: Dict[int, Dict[str, float]],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get AI-recommended budget distribution."""
    optimizer = SmartOptimizer(db)
    
    metrics = {}
    for cid, m in campaign_metrics.items():
        metrics[int(cid)] = PerformanceMetrics(
            impressions=m.get("impressions", 0),
            clicks=m.get("clicks", 0),
            conversions=m.get("conversions", 0),
            spend=m.get("spend", 0.0),
            revenue=m.get("revenue", 0.0),
        )
    
    allocations = await optimizer.get_budget_recommendations(
        organization_id=current_user.active_organization_id,
        total_budget=total_budget,
        campaign_metrics=metrics,
    )
    
    return {
        "total_budget": total_budget,
        "allocations": {str(k): v for k, v in allocations.items()},
    }


# =============================================================================
# COMPETITOR ENDPOINTS
# =============================================================================

@router.post("/competitor/analyze")
async def analyze_competitor(
    payload: CompetitorRequest,
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    """Analyze a competitor domain."""
    intel = CompetitorIntelligence()
    
    try:
        analysis = await intel.analyze_competitor(payload.domain)

        try:
            rag = RagService(db)
            summary_lines = [
                analysis.profile.description or "",
                f"Продукты: {', '.join(analysis.profile.products or [])}" if analysis.profile.products else "",
                f"Сильные стороны: {', '.join(analysis.strengths or [])}" if analysis.strengths else "",
                f"Слабые стороны: {', '.join(analysis.weaknesses or [])}" if analysis.weaknesses else "",
                f"Возможности: {', '.join(analysis.opportunities or [])}" if analysis.opportunities else "",
                f"Рекомендации: {', '.join(analysis.recommendations or [])}" if analysis.recommendations else "",
                f"Ключевые слова: {', '.join(analysis.keywords or [])}" if analysis.keywords else "",
            ]
            rag_text = "\n".join([line for line in summary_lines if line]).strip()
            if rag_text:
                await rag.ingest_text(
                    organization_id=org.id,
                    source_type="competitor",
                    title=analysis.profile.name or analysis.domain,
                    url=f"https://{analysis.domain}",
                    text=rag_text,
                    meta={
                        "keywords": analysis.keywords,
                        "strengths": analysis.strengths,
                        "weaknesses": analysis.weaknesses,
                        "opportunities": analysis.opportunities,
                        "recommendations": analysis.recommendations,
                    },
                )
        except Exception:
            logger.exception("Failed to ingest competitor into RAG")
        
        return {
            "domain": analysis.domain,
            "profile": {
                "name": analysis.profile.name,
                "description": analysis.profile.description,
                "products": analysis.profile.products,
                "trust_signals": analysis.profile.trust_signals,
                "social_links": analysis.profile.social_links,
            },
            "keywords": analysis.keywords,
            "strengths": analysis.strengths,
            "weaknesses": analysis.weaknesses,
            "opportunities": analysis.opportunities,
            "recommendations": analysis.recommendations,
            "analyzed_at": analysis.analyzed_at.isoformat(),
        }
    finally:
        await intel.close()


@router.post("/competitor/compare")
async def compare_with_competitor(
    payload: CompetitorCompareRequest,
    current_user: User = Depends(get_current_user),
):
    """Compare your domain with a competitor."""
    intel = CompetitorIntelligence()
    
    try:
        result = await intel.compare_with_competitor(
            payload.my_domain,
            payload.competitor_domain,
        )
        return result
    finally:
        await intel.close()


@router.post("/competitor/find")
async def find_competitors(
    domain: str,
    industry: str,
    current_user: User = Depends(get_current_user),
):
    """Find potential competitors."""
    intel = CompetitorIntelligence()
    
    try:
        competitors = await intel.find_competitors(domain, industry)
        return {"competitors": competitors}
    finally:
        await intel.close()


# =============================================================================
# CREATIVE STUDIO ENDPOINTS
# =============================================================================

@router.post("/creative/variations")
async def generate_variations(
    payload: VariationsRequest,
    current_user: User = Depends(get_current_user),
):
    """Generate creative variations."""
    studio = CreativeStudio()
    
    try:
        bundle = await studio.generate_variations(
            original_title=payload.title,
            original_text=payload.text,
            count=min(payload.count, 100),
            target_platform=payload.platform,
            business_context=payload.business_context,
        )
        
        return {
            "original_title": bundle.original_title,
            "original_text": bundle.original_text,
            "variations": [
                {
                    "id": v.id,
                    "title": v.title,
                    "text": v.text,
                    "approach": v.approach,
                }
                for v in bundle.variations
            ],
            "count": len(bundle.variations),
            "generated_at": bundle.generated_at.isoformat(),
        }
    finally:
        await studio.close()


@router.post("/creative/predict")
async def predict_performance(
    payload: PredictRequest,
    current_user: User = Depends(get_current_user),
):
    """Predict creative performance."""
    studio = CreativeStudio()
    
    try:
        prediction = await studio.predict_performance(
            title=payload.title,
            text=payload.text,
            industry=payload.industry,
            target_audience=payload.target_audience,
        )
        return prediction
    finally:
        await studio.close()


@router.post("/creative/ab-suggestions")
async def suggest_ab_tests(
    payload: ABTestSuggestRequest,
    current_user: User = Depends(get_current_user),
):
    """Get A/B test suggestions for a creative."""
    studio = CreativeStudio()
    
    try:
        suggestions = await studio.suggest_ab_tests(
            title=payload.title,
            text=payload.text,
        )
        return {"tests": suggestions}
    finally:
        await studio.close()


@router.post("/creative/image-prompts")
async def generate_image_prompts(
    title: str,
    text: str,
    business_type: str,
    count: int = 5,
    current_user: User = Depends(get_current_user),
):
    """Generate DALL-E prompts for ad images."""
    studio = CreativeStudio()
    
    try:
        prompts = await studio.generate_image_prompts(
            title=title,
            text=text,
            business_type=business_type,
            count=min(count, 10),
        )
        return {"prompts": prompts}
    finally:
        await studio.close()


# =============================================================================
# CASCADE GENERATION ENDPOINTS
# =============================================================================

class CascadeRequest(BaseModel):
    landing_url: str
    platform: str = "yandex"
    description: Optional[str] = None
    generate_images: bool = True
    image_count: int = 3


@router.post("/cascade/generate")
async def cascade_generate(
    payload: CascadeRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Cascade generation: scan → text → image prompts → DALL-E.
    
    Full pipeline that scans a landing page, generates ad texts,
    creates image prompts, and generates images with DALL-E.
    """
    pipeline = CascadeImagePipeline()
    
    try:
        result = await pipeline.generate(
            landing_url=payload.landing_url,
            platform=payload.platform,
            description=payload.description,
            generate_images=payload.generate_images,
            image_count=min(payload.image_count, 5),
        )
        
        return {
            "business_name": result.business_name,
            "business_type": result.business_type,
            "landing_url": result.landing_url,
            "platform": result.platform,
            "creatives": [
                {
                    "title": c.title,
                    "text": c.text,
                    "approach": c.approach,
                    "image_prompt": c.image_prompt,
                    "image_url": c.image_url,
                }
                for c in result.creatives
            ],
            "creatives_count": len(result.creatives),
            "images_generated": sum(1 for c in result.creatives if c.image_url),
            "generated_at": result.generated_at.isoformat(),
        }
    finally:
        await pipeline.close()


# =============================================================================
# UTM BUILDER ENDPOINTS
# =============================================================================

class UTMRequest(BaseModel):
    base_url: str
    utm_source: str
    utm_medium: str
    utm_campaign: str
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None


class UTMPlatformRequest(BaseModel):
    base_url: str
    platform: str
    campaign_name: str
    ad_id: Optional[str] = None
    keyword: Optional[str] = None


@router.post("/utm/build")
async def build_utm_url(
    payload: UTMRequest,
    current_user: User = Depends(get_current_user),
):
    """Build URL with UTM parameters."""
    url = UTMBuilder.build_url(
        base_url=payload.base_url,
        utm_source=payload.utm_source,
        utm_medium=payload.utm_medium,
        utm_campaign=payload.utm_campaign,
        utm_term=payload.utm_term,
        utm_content=payload.utm_content,
    )
    return {"url": url}


@router.post("/utm/platform")
async def build_platform_utm(
    payload: UTMPlatformRequest,
    current_user: User = Depends(get_current_user),
):
    """Build URL using platform-specific template."""
    url = UTMBuilder.from_platform(
        base_url=payload.base_url,
        platform=payload.platform,
        campaign_name=payload.campaign_name,
        ad_id=payload.ad_id,
        keyword=payload.keyword,
    )
    return {"url": url, "platform": payload.platform}
