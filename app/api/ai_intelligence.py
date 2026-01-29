"""
AI Intelligence API

Advanced AI-powered features for competitive advantage.
"""
import json
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import asyncio

from app.api.deps import get_db, get_current_user, get_current_org_id
from app.db.models import User
from app.services.ai_intelligence import (
    get_competitor_analyzer,
    get_roi_predictor,
    get_creative_scorer,
    get_audience_finder,
    get_voice_assistant
)

router = APIRouter(prefix="/ai", tags=["AI Intelligence"])


# =============================================================================
# SCHEMAS
# =============================================================================

class CompetitorAnalysisRequest(BaseModel):
    competitor_url: str = Field(..., description="Competitor website URL")
    your_business: str = Field(..., description="Description of your business")


class MultiCompetitorRequest(BaseModel):
    competitor_urls: List[str] = Field(..., max_items=5)
    your_business: str


class ROIPredictionRequest(BaseModel):
    budget: float = Field(..., ge=1000, le=100000000)
    industry: str = Field(default="default")
    business_description: str
    target_audience: Optional[str] = None
    platforms: Optional[List[str]] = None


class CreativeScoringRequest(BaseModel):
    title: str
    text: str
    platform: str = "yandex"
    landing_url: Optional[str] = None


class BatchScoringRequest(BaseModel):
    creatives: List[Dict[str, str]]
    platform: str = "yandex"


class AudienceFinderRequest(BaseModel):
    business_description: str
    current_targeting: Optional[str] = None
    platforms: Optional[List[str]] = None


class KeywordExpansionRequest(BaseModel):
    seed_keywords: List[str]
    business_type: str


class VoiceCommandRequest(BaseModel):
    command: str
    context: Optional[Dict[str, Any]] = None


# =============================================================================
# COMPETITOR ANALYSIS
# =============================================================================

@router.post("/competitors/analyze")
async def analyze_competitor(
    payload: CompetitorAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze a single competitor and get strategic insights.

    Uses AI to:
    - Scrape competitor website
    - Identify strengths and weaknesses
    - Find opportunities for your business
    - Generate counter-strategies
    - Suggest ad copy angles
    """
    analyzer = get_competitor_analyzer()

    try:
        result = await analyzer.analyze_competitor(
            competitor_url=payload.competitor_url,
            your_business=payload.your_business
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/competitors/analyze-multiple")
async def analyze_multiple_competitors(
    payload: MultiCompetitorRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze multiple competitors and synthesize a unified strategy.

    Compares up to 5 competitors and provides:
    - Individual analyses
    - Market positioning insights
    - Priority action items
    - Budget allocation recommendations
    """
    analyzer = get_competitor_analyzer()

    try:
        result = await analyzer.analyze_multiple(
            competitor_urls=payload.competitor_urls,
            your_business=payload.your_business
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/competitors/analyze-stream")
async def analyze_competitor_stream(
    payload: CompetitorAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """Stream competitor analysis with real-time updates."""

    async def generate():
        analyzer = get_competitor_analyzer()

        yield f"data: {json.dumps({'type': 'status', 'message': 'Scanning competitor website...'})}\n\n"
        await asyncio.sleep(0.5)

        yield f"data: {json.dumps({'type': 'status', 'message': 'Analyzing business model...'})}\n\n"
        await asyncio.sleep(0.5)

        try:
            result = await analyzer.analyze_competitor(
                payload.competitor_url,
                payload.your_business
            )

            yield f"data: {json.dumps({'type': 'status', 'message': 'Generating insights...'})}\n\n"
            yield f"data: {json.dumps({'type': 'result', 'data': result})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


# =============================================================================
# ROI PREDICTION
# =============================================================================

@router.post("/predict/roi")
async def predict_roi(
    payload: ROIPredictionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Predict ROI for a given budget and business.

    Returns:
    - Expected impressions, clicks, conversions
    - Revenue projections
    - Pessimistic/Realistic/Optimistic scenarios
    - Break-even analysis
    - AI-powered recommendations
    """
    predictor = get_roi_predictor()

    try:
        result = await predictor.predict_roi(
            budget=payload.budget,
            industry=payload.industry,
            business_description=payload.business_description,
            target_audience=payload.target_audience,
            platforms=payload.platforms
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predict/industries")
async def get_industries():
    """Get list of supported industries with benchmarks."""
    predictor = get_roi_predictor()

    return {
        "industries": [
            {"id": "ecommerce", "name": "E-commerce / Интернет-магазины"},
            {"id": "services", "name": "Услуги"},
            {"id": "saas", "name": "SaaS / IT продукты"},
            {"id": "education", "name": "Образование"},
            {"id": "realestate", "name": "Недвижимость"},
            {"id": "auto", "name": "Авто"},
            {"id": "beauty", "name": "Красота / Здоровье"},
            {"id": "default", "name": "Другое"}
        ],
        "benchmarks": predictor.INDUSTRY_BENCHMARKS
    }


# =============================================================================
# CREATIVE SCORING
# =============================================================================

@router.post("/creatives/score")
async def score_creative(
    payload: CreativeScoringRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Score a creative and get improvement suggestions.

    Evaluates:
    - Headline effectiveness
    - Clarity and readability
    - Emotional appeal
    - Call-to-action strength
    - Platform compliance

    Returns A/B test variants for optimization.
    """
    scorer = get_creative_scorer()

    try:
        result = await scorer.score_creative(
            title=payload.title,
            text=payload.text,
            platform=payload.platform,
            landing_url=payload.landing_url
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/creatives/score-batch")
async def score_creatives_batch(
    payload: BatchScoringRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Score multiple creatives and rank them.

    Returns:
    - Ranked list of creatives by score
    - Best performing creative
    - Overall recommendations
    """
    scorer = get_creative_scorer()

    try:
        result = await scorer.score_batch(
            creatives=payload.creatives,
            platform=payload.platform
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# AUDIENCE DISCOVERY
# =============================================================================

@router.post("/audiences/discover")
async def discover_audiences(
    payload: AudienceFinderRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Discover target audiences for your business.

    Returns:
    - Primary and secondary audiences
    - Demographic profiles
    - Interest and behavior targeting
    - Hidden opportunities
    - Platform-specific targeting suggestions
    """
    finder = get_audience_finder()

    try:
        result = await finder.find_audiences(
            business_description=payload.business_description,
            current_targeting=payload.current_targeting,
            platforms=payload.platforms
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audiences/expand-keywords")
async def expand_keywords(
    payload: KeywordExpansionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Expand seed keywords using AI.

    Returns:
    - Expanded keyword list with intent and competition
    - Long-tail variations
    - Negative keywords
    - Keyword clusters by theme
    """
    finder = get_audience_finder()

    try:
        result = await finder.expand_keywords(
            seed_keywords=payload.seed_keywords,
            business_type=payload.business_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# VOICE ASSISTANT
# =============================================================================

@router.post("/voice/command")
async def process_voice_command(
    payload: VoiceCommandRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: int = Depends(get_current_org_id)
):
    """
    Process a voice command and return action.

    Supported commands:
    - "Покажи статистику за сегодня"
    - "Какой CTR у моих кампаний?"
    - "Увеличь бюджет на 20%"
    - "Создай новую кампанию"
    - "Останови рекламу"
    - "Дай рекомендации"
    """
    assistant = get_voice_assistant()

    try:
        # Add user context
        context = payload.context or {}
        context["org_id"] = org_id
        context["user_id"] = current_user.id

        # Parse intent
        intent = await assistant.process_command(
            command=payload.command,
            context=context
        )

        # Generate response
        response_text = await assistant.generate_response(intent)

        return {
            "intent": intent,
            "response": response_text,
            "action_required": intent.get("intent") not in ["get_stats", "unknown"],
            "clarification_needed": intent.get("clarification_needed")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# COMBINED INTELLIGENCE
# =============================================================================

@router.post("/full-analysis")
async def full_business_analysis(
    business_description: str,
    competitor_urls: Optional[List[str]] = None,
    budget: float = 50000,
    current_user: User = Depends(get_current_user)
):
    """
    Run a comprehensive AI analysis of your business.

    Combines:
    - Competitor analysis
    - ROI prediction
    - Audience discovery
    - Creative scoring (if creatives provided)

    Returns a complete strategic plan.
    """
    results = {}

    # Parallel execution
    tasks = []

    # ROI Prediction
    predictor = get_roi_predictor()
    tasks.append(predictor.predict_roi(
        budget=budget,
        industry="default",
        business_description=business_description
    ))

    # Audience Discovery
    finder = get_audience_finder()
    tasks.append(finder.find_audiences(
        business_description=business_description
    ))

    # Competitor Analysis (if URLs provided)
    if competitor_urls:
        analyzer = get_competitor_analyzer()
        tasks.append(analyzer.analyze_multiple(
            competitor_urls=competitor_urls[:3],
            your_business=business_description
        ))

    # Execute all
    all_results = await asyncio.gather(*tasks, return_exceptions=True)

    results["roi_prediction"] = all_results[0] if not isinstance(all_results[0], Exception) else None
    results["audiences"] = all_results[1] if not isinstance(all_results[1], Exception) else None
    if len(all_results) > 2:
        results["competitor_analysis"] = all_results[2] if not isinstance(all_results[2], Exception) else None

    return {
        "business": business_description,
        "budget": budget,
        "analysis": results,
        "status": "complete"
    }
