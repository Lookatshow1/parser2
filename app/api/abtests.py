"""
A/B Testing API Endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.api.deps import get_current_org_id
from app.services.abtests import ABTestService
from app.api.abtests_schemas import (
    ABTestCreate, ABTestResponse, SignificanceResponse, MetricsUpdate, VariantResponse
)


router = APIRouter(prefix="/abtests", tags=["A/B Tests"])


@router.post("", response_model=ABTestResponse)
async def create_ab_test(
    data: ABTestCreate,
    session: AsyncSession = Depends(get_session),
    org_id: int = Depends(get_current_org_id)
):
    """Создать новый A/B тест."""
    service = ABTestService(session)
    test = await service.create_test(
        organization_id=org_id,
        name=data.name,
        description=data.description,
        variants=[v.dict() for v in data.variants],
        primary_metric=data.primary_metric,
        min_sample_size=data.min_sample_size,
        confidence_level=data.confidence_level
    )
    return test


@router.get("", response_model=List[ABTestResponse])
async def list_ab_tests(
    status: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    org_id: int = Depends(get_current_org_id)
):
    """Получить список A/B тестов."""
    service = ABTestService(session)
    tests = await service.list_tests(org_id, status)
    return tests


@router.get("/{test_id}", response_model=ABTestResponse)
async def get_ab_test(
    test_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Получить A/B тест по ID."""
    service = ABTestService(session)
    test = await service.get_test(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")
    return test


@router.post("/{test_id}/start", response_model=ABTestResponse)
async def start_ab_test(
    test_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Запустить A/B тест."""
    service = ABTestService(session)
    try:
        test = await service.start_test(test_id)
        return test
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{test_id}/pause", response_model=ABTestResponse)
async def pause_ab_test(
    test_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Приостановить A/B тест."""
    service = ABTestService(session)
    try:
        test = await service.pause_test(test_id)
        return test
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{test_id}/significance", response_model=SignificanceResponse)
async def get_significance(
    test_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Получить статистическую значимость теста."""
    service = ABTestService(session)
    return await service.calculate_significance(test_id)


@router.post("/{test_id}/select-winner/{variant_id}", response_model=ABTestResponse)
async def select_winner(
    test_id: int,
    variant_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Выбрать победителя теста."""
    service = ABTestService(session)
    try:
        test = await service.select_winner(test_id, variant_id)
        return test
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{test_id}/auto-select-winner", response_model=ABTestResponse)
async def auto_select_winner(
    test_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Автоматически выбрать победителя, если есть статистическая значимость."""
    service = ABTestService(session)
    test = await service.auto_select_winner(test_id)
    if not test:
        raise HTTPException(status_code=400, detail="Нет статистической значимости для выбора победителя")
    return test


@router.patch("/variants/{variant_id}/metrics", response_model=VariantResponse)
async def update_variant_metrics(
    variant_id: int,
    metrics: MetricsUpdate,
    session: AsyncSession = Depends(get_session)
):
    """Обновить метрики варианта (используется синхронизацией)."""
    service = ABTestService(session)
    try:
        variant = await service.update_metrics(variant_id, metrics.dict())
        return variant
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
