"""
Magic Launch API

One-click campaign launch endpoints.
The "Money Button" API.
"""
import asyncio
import json as json_module
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.api.deps import get_db, get_current_user, get_current_org_id
from app.db.models import User
from app.services.magic_launch import MagicLaunchService, get_magic_launch_service
from app.core.ai.orchestrator import get_orchestrator, MultiAIOrchestrator

# Global orchestrator instance to avoid re-initialization overhead
_orchestrator: Optional[MultiAIOrchestrator] = None

def get_global_orchestrator() -> MultiAIOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = get_orchestrator()
    return _orchestrator

router = APIRouter(prefix="/magic-launch", tags=["Magic Launch"])


# =============================================================================
# SCHEMAS
# =============================================================================

class MagicLaunchRequest(BaseModel):
    """Request for Magic Launch - the Money Button."""
    landing_url: Optional[str] = Field(None, description="Website URL to analyze")
    business_description: Optional[str] = Field(None, description="Business description")
    budget: float = Field(10000, ge=1000, le=10000000, description="Total budget in RUB")
    platforms: Optional[List[str]] = Field(None, description="Target platforms")
    auto_start: bool = Field(True, description="Start campaigns immediately")

    # Creative options
    generate_images: bool = Field(True, description="Generate ad images")
    generate_voice: bool = Field(False, description="Generate voiceovers")
    generate_video: bool = Field(False, description="Generate video ads")


class PlatformResult(BaseModel):
    platform: str
    status: str
    draft_campaign_id: Optional[int] = None
    external_id: Optional[str] = None
    budget: float
    ads_count: int
    message: Optional[str] = None
    launch_error: Optional[str] = None


class CreativesInfo(BaseModel):
    ads_count: int
    images_count: int
    voiceovers_count: int
    videos_count: int


class MagicLaunchResponse(BaseModel):
    """Response from Magic Launch."""
    status: str
    business_name: Optional[str] = None
    total_budget: float
    budget_launched: float
    platforms_launched: int
    platforms_total: int
    campaigns: List[PlatformResult]
    creatives: CreativesInfo
    ai_provider: Optional[str] = None
    launched_at: str


class EstimateRequest(BaseModel):
    """Request for results estimation."""
    budget: float = Field(10000, ge=1000)
    platforms: List[str] = Field(default=["yandex", "vk"])
    business_type: str = Field(default="services")


class PlatformEstimate(BaseModel):
    impressions: int
    clicks: int
    leads: int
    budget: float


class EstimateResponse(BaseModel):
    """Estimated campaign results."""
    total: PlatformEstimate
    by_platform: Dict[str, PlatformEstimate]
    disclaimer: str


class QuickGenerateRequest(BaseModel):
    """Quick creative generation without launch."""
    landing_url: Optional[str] = None
    business_description: Optional[str] = None
    generate_images: bool = True


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/launch", response_model=MagicLaunchResponse)
async def magic_launch(
    payload: MagicLaunchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: int = Depends(get_current_org_id)
):
    """
    Magic Launch - One-click advertising.

    This is the "Money Button". Provide a URL or description,
    set your budget, and launch ads across all platforms instantly.

    Flow:
    1. AI analyzes your business
    2. Generates optimized ad creatives
    3. Creates campaigns on all platforms
    4. Launches with smart budget distribution
    5. You start getting leads

    Minimum input, maximum output.
    """
    service = get_magic_launch_service(db)

    creative_options = {
        "images": payload.generate_images,
        "voice": payload.generate_voice,
        "video": payload.generate_video
    }

    result = await service.magic_launch(
        org_id=org_id,
        user_id=current_user.id,
        landing_url=payload.landing_url,
        business_description=payload.business_description,
        budget=payload.budget,
        platforms=payload.platforms,
        auto_start=payload.auto_start,
        creative_options=creative_options
    )

    if result["status"] == "error":
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Launch failed")
        )

    return result


@router.post("/launch-stream")
async def magic_launch_stream(
    payload: MagicLaunchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: int = Depends(get_current_org_id)
):
    """
    Magic Launch with SSE streaming for real-time progress updates.

    Returns Server-Sent Events with progress:
    - step: Current step name
    - progress: Percentage complete
    - result: Final result when done
    """
    async def event_generator():
        service = get_magic_launch_service(db)
        orchestrator = get_global_orchestrator()

        try:
            # Step 1: Analyzing
            yield f"data: {json_module.dumps({'type': 'step', 'step': 1, 'total': 5, 'message': 'Analyzing your business...'})}\n\n"
            yield f"data: {json_module.dumps({'type': 'progress', 'percent': 10})}\n\n"
            # Removed artificial sleep for speed

            # Step 2: Generating creatives
            yield f"data: {json_module.dumps({'type': 'step', 'step': 2, 'total': 5, 'message': 'AI is creating ad creatives...'})}\n\n"

            creative_options = {
                "images": payload.generate_images,
                "voice": payload.generate_voice,
                "video": payload.generate_video
            }

            # Generate creatives
            campaign_data = await orchestrator.generate_full_campaign(
                business_info=payload.business_description or "",
                landing_url=payload.landing_url or "",
                budget=payload.budget,
                platforms=payload.platforms or ["yandex", "vk"],
                creative_options=creative_options
            )

            yield f"data: {json_module.dumps({'type': 'progress', 'percent': 50})}\n\n"
            yield f"data: {json_module.dumps({'type': 'creatives', 'count': len(campaign_data['creatives'].get('ads', []))})}\n\n"

            # Step 3: Creating campaigns
            yield f"data: {json_module.dumps({'type': 'step', 'step': 3, 'total': 5, 'message': 'Creating campaigns on platforms...'})}\n\n"
            yield f"data: {json_module.dumps({'type': 'progress', 'percent': 70})}\n\n"

            # Step 4: Launching
            yield f"data: {json_module.dumps({'type': 'step', 'step': 4, 'total': 5, 'message': 'Launching campaigns...'})}\n\n"

            # Execute full launch
            result = await service.magic_launch(
                org_id=org_id,
                user_id=current_user.id,
                landing_url=payload.landing_url,
                business_description=payload.business_description,
                budget=payload.budget,
                platforms=payload.platforms,
                auto_start=payload.auto_start,
                creative_options=creative_options
            )

            yield f"data: {json_module.dumps({'type': 'progress', 'percent': 90})}\n\n"

            # Step 5: Done
            yield f"data: {json_module.dumps({'type': 'step', 'step': 5, 'total': 5, 'message': 'Launch complete!'})}\n\n"
            yield f"data: {json_module.dumps({'type': 'progress', 'percent': 100})}\n\n"

            yield f"data: {json_module.dumps({'type': 'result', 'data': result})}\n\n"
            yield f"data: {json_module.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json_module.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/estimate", response_model=EstimateResponse)
async def estimate_results(
    payload: EstimateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Estimate campaign results before launch.

    Returns predicted impressions, clicks, and leads
    based on budget and platforms.
    """
    service = get_magic_launch_service(db)

    result = await service.estimate_results(
        budget=payload.budget,
        platforms=payload.platforms,
        business_type=payload.business_type
    )

    return result


@router.post("/quick-generate")
async def quick_generate(
    payload: QuickGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Quick creative generation without creating a campaign.

    Use this to preview what AI will generate before committing.
    No authentication required for demo purposes.
    """
    orchestrator = get_orchestrator()

    try:
        result = await orchestrator.generate_ad_creatives(
            business_info=payload.business_description or "",
            landing_url=payload.landing_url,
            generate_images=payload.generate_images,
            generate_voice=False,
            generate_video=False
        )

        return {
            "status": "success",
            "business_name": result.get("business_name"),
            "business_type": result.get("business_type"),
            "ads": result.get("ads", []),
            "images": result.get("images", []),
            "provider": result.get("text_provider")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/platforms")
async def get_available_platforms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org_id: int = Depends(get_current_org_id)
):
    """
    Get available platforms for Magic Launch.

    Returns platforms with active connections.
    """
    from app.db.models import Connection

    connections = db.query(Connection).filter(
        Connection.organization_id == org_id,
        Connection.status == "active"
    ).all()

    platforms = []
    for conn in connections:
        platforms.append({
            "platform": conn.platform.value if hasattr(conn.platform, 'value') else conn.platform,
            "name": conn.name,
            "connection_id": conn.id,
            "status": conn.status
        })

    # Add mock platforms if none connected
    if not platforms:
        platforms = [
            {"platform": "yandex", "name": "Yandex Direct (Demo)", "connection_id": None, "status": "demo"},
            {"platform": "vk", "name": "VK Ads (Demo)", "connection_id": None, "status": "demo"}
        ]

    return {
        "platforms": platforms,
        "total": len(platforms)
    }


@router.get("/ai-status")
async def get_ai_status():
    """
    Get status of AI providers.

    Returns which AI models are available and their status.
    """
    import os

    providers = {
        "gigachat": {
            "name": "GigaChat (Sber)",
            "available": bool(os.getenv("GIGACHAT_AUTH_KEY")),
            "requires_proxy": False,
            "best_for": "Russian language, works in Russia"
        },
        "openrouter": {
            "name": "OpenRouter (100+ models)",
            "available": bool(os.getenv("OPENROUTER_API_KEY")),
            "requires_proxy": True,
            "best_for": "GPT-4, Claude, Mixtral, etc."
        },
        "openai": {
            "name": "OpenAI Direct",
            "available": bool(os.getenv("OPENAI_API_KEY")),
            "requires_proxy": True,
            "best_for": "GPT-4, DALL-E"
        },
        "anthropic": {
            "name": "Anthropic Direct",
            "available": bool(os.getenv("ANTHROPIC_API_KEY")),
            "requires_proxy": True,
            "best_for": "Claude"
        },
        "elevenlabs": {
            "name": "ElevenLabs Voice",
            "available": bool(os.getenv("ELEVENLABS_API_KEY")),
            "requires_proxy": False,
            "best_for": "Voice generation"
        },
        "heygen": {
            "name": "HeyGen Video",
            "available": bool(os.getenv("HEYGEN_API_KEY")),
            "requires_proxy": False,
            "best_for": "AI video ads"
        }
    }

    available_count = sum(1 for p in providers.values() if p["available"])

    return {
        "providers": providers,
        "available_count": available_count,
        "total_count": len(providers),
        "proxy_configured": bool(os.getenv("OPENROUTER_PROXY_URL") or os.getenv("AI_PROXY_URL"))
    }
