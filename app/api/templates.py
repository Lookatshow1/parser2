"""
Industry Templates API Endpoints.

Get templates and benchmarks by industry.
"""
from fastapi import APIRouter, Query
from typing import Optional, List
from pydantic import BaseModel

from app.services.industry_templates import (
    Industry, get_benchmark, get_templates, get_all_industries, compare_with_benchmark
)

router = APIRouter(prefix="/templates", tags=["Templates"])


# =============================================================================
# SCHEMAS
# =============================================================================

class IndustryItem(BaseModel):
    id: str
    name: str


class BenchmarkResponse(BaseModel):
    industry: str
    avg_ctr: float
    avg_cpc: float
    avg_cpa: float
    avg_roas: float
    conversion_rate: float


class AdTemplateResponse(BaseModel):
    title: str
    text: str
    approach: str


class CampaignTemplateResponse(BaseModel):
    name: str
    description: str
    recommended_budget: int
    recommended_bid: int
    keywords: List[str]
    negative_keywords: List[str]
    ads: List[AdTemplateResponse]
    tips: List[str]


class CompareResponse(BaseModel):
    industry: str
    ctr: dict
    cpc: dict
    cpa: Optional[dict] = None


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/industries", response_model=List[IndustryItem])
def list_industries():
    """Получить список всех поддерживаемых отраслей."""
    return get_all_industries()


@router.get("/benchmarks/{industry}", response_model=BenchmarkResponse)
def get_industry_benchmark(industry: str):
    """Получить бенчмарки по отрасли."""
    try:
        ind = Industry(industry)
    except ValueError:
        return {"error": f"Unknown industry: {industry}"}
    
    benchmark = get_benchmark(ind)
    if not benchmark:
        return {"error": "Benchmark not found"}
    
    return BenchmarkResponse(
        industry=benchmark.industry.value,
        avg_ctr=benchmark.avg_ctr,
        avg_cpc=benchmark.avg_cpc,
        avg_cpa=benchmark.avg_cpa,
        avg_roas=benchmark.avg_roas,
        conversion_rate=benchmark.conversion_rate,
    )


@router.get("/campaigns/{industry}", response_model=List[CampaignTemplateResponse])
def get_industry_templates(industry: str):
    """Получить шаблоны кампаний для отрасли."""
    try:
        ind = Industry(industry)
    except ValueError:
        return []
    
    templates = get_templates(ind)
    return [
        CampaignTemplateResponse(
            name=t.name,
            description=t.description,
            recommended_budget=t.recommended_budget,
            recommended_bid=t.recommended_bid,
            keywords=t.keywords,
            negative_keywords=t.negative_keywords,
            ads=[AdTemplateResponse(title=a.title, text=a.text, approach=a.approach) for a in t.ads],
            tips=t.tips,
        )
        for t in templates
    ]


@router.get("/compare", response_model=CompareResponse)
def compare_metrics(
    industry: str = Query(..., description="Отрасль"),
    ctr: float = Query(..., description="Фактический CTR в %"),
    cpc: float = Query(..., description="Фактический CPC в рублях"),
    cpa: Optional[float] = Query(None, description="Фактический CPA в рублях"),
):
    """Сравнить метрики с бенчмарками отрасли."""
    try:
        ind = Industry(industry)
    except ValueError:
        return {"industry": industry, "error": "Unknown industry"}
    
    return compare_with_benchmark(ind, ctr, cpc, cpa)
