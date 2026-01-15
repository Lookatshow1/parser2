"""
Тесты для KPI дашборда
"""
import pytest
from datetime import date, timedelta
from app.services.dashboard_service import build_kpi_timeseries, build_kpi_summary
from app.db.models import MetricSnapshot, Connection, Platform, Organization
from sqlalchemy.orm import Session


@pytest.fixture
def org_a(session: Session):
    from app.db.models import Organization
    org = Organization(name="Org A")
    session.add(org)
    session.commit()
    session.refresh(org)
    return org


@pytest.fixture
def connection_yandex(session: Session, org_a: Organization):
    conn = Connection(
        organization_id=org_a.id,
        name="Yandex Connection",
        platform=Platform.yandex,
        credentials_json={}
    )
    session.add(conn)
    session.commit()
    session.refresh(conn)
    return conn


@pytest.fixture
def metric_snapshots(session: Session, org_a: Organization, connection_yandex: Connection):
    """Создать тестовые метрики"""
    today = date.today()
    snapshots = []
    
    for i in range(5):
        snapshot = MetricSnapshot(
            organization_id=org_a.id,
            connection_id=connection_yandex.id,
            platform=Platform.yandex,
            date=today - timedelta(days=4-i),
            level="campaign",
            campaign_external_id="camp_1",
            impressions=1000 + i * 100,
            clicks=50 + i * 10,
            purchases=i + 1,  # conversions
            spend=5000 + i * 500
        )
        session.add(snapshot)
        snapshots.append(snapshot)
    
    session.commit()
    return snapshots


def test_kpi_timeseries_index_mode(session: Session, org_a: Organization, connection_yandex: Connection, metric_snapshots):
    """Тест таймсерии в режиме индексов"""
    today = date.today()
    result = build_kpi_timeseries(
        db=session,
        org_id=org_a.id,
        date_from=today - timedelta(days=5),
        date_to=today,
        connection_ids=[connection_yandex.id],
        platform=None,
        mode="index"
    )
    
    assert "items" in result
    assert "meta" in result
    assert result["meta"]["mode"] == "index"
    
    items = result["items"]
    assert len(items) == 5
    
    # Проверяем, что индексы нормализованы (0-100)
    for item in items:
        assert item["impressions_index"] is not None
        assert item["clicks_index"] is not None
        assert item["conversions_index"] is not None
        assert item["spend_index"] is not None
        assert 0 <= item["impressions_index"] <= 100
        assert 0 <= item["clicks_index"] <= 100
        assert 0 <= item["conversions_index"] <= 100
        assert 0 <= item["spend_index"] <= 100
    
    # Максимальное значение должно быть 100
    max_impressions_index = max(item["impressions_index"] for item in items)
    max_clicks_index = max(item["clicks_index"] for item in items)
    max_conversions_index = max(item["conversions_index"] for item in items)
    max_spend_index = max(item["spend_index"] for item in items)
    
    assert max_impressions_index == 100.0
    assert max_clicks_index == 100.0
    assert max_conversions_index == 100.0
    assert max_spend_index == 100.0


def test_kpi_timeseries_absolute_mode(session: Session, org_a: Organization, connection_yandex: Connection, metric_snapshots):
    """Тест таймсерии в режиме абсолютных значений"""
    today = date.today()
    result = build_kpi_timeseries(
        db=session,
        org_id=org_a.id,
        date_from=today - timedelta(days=5),
        date_to=today,
        connection_ids=[connection_yandex.id],
        platform=None,
        mode="absolute"
    )
    
    assert "items" in result
    assert result["meta"]["mode"] == "absolute"
    
    items = result["items"]
    assert len(items) == 5
    
    # Проверяем, что индексы None в absolute режиме
    for item in items:
        assert item["impressions_index"] is None
        assert item["clicks_index"] is None
        assert item["conversions_index"] is None
        assert item["spend_index"] is None
        # Проверяем абсолютные значения
        assert item["impressions"] > 0
        assert item["clicks"] > 0
        assert item["conversions"] > 0
        assert item["spend"] > 0


def test_kpi_timeseries_platform_filter(session: Session, org_a: Organization, connection_yandex: Connection, metric_snapshots):
    """Тест фильтрации по платформе"""
    today = date.today()
    
    # Все каналы
    result_all = build_kpi_timeseries(
        db=session,
        org_id=org_a.id,
        date_from=today - timedelta(days=5),
        date_to=today,
        connection_ids=[connection_yandex.id],
        platform=None,
        mode="index"
    )
    
    # Только Яндекс
    result_yandex = build_kpi_timeseries(
        db=session,
        org_id=org_a.id,
        date_from=today - timedelta(days=5),
        date_to=today,
        connection_ids=[connection_yandex.id],
        platform="yandex",
        mode="index"
    )
    
    # Результаты должны быть одинаковыми (все метрики из yandex)
    assert len(result_all["items"]) == len(result_yandex["items"])


def test_kpi_summary_calculates_metrics(session: Session, org_a: Organization, connection_yandex: Connection, metric_snapshots):
    """Тест сводки KPI с корректным расчётом метрик"""
    today = date.today()
    result = build_kpi_summary(
        db=session,
        org_id=org_a.id,
        date_from=today - timedelta(days=5),
        date_to=today,
        connection_ids=[connection_yandex.id],
        platform=None
    )
    
    assert "impressions" in result
    assert "clicks" in result
    assert "conversions" in result
    assert "spend" in result
    assert "ctr" in result
    assert "cpc" in result
    assert "cpa" in result
    assert "currency" in result
    
    # Проверяем, что метрики не пустые
    assert result["impressions"] > 0
    assert result["clicks"] > 0
    assert result["conversions"] > 0
    assert result["spend"] > 0
    
    # Проверяем расчёт CTR
    expected_ctr = round((result["clicks"] / result["impressions"] * 100), 2)
    assert result["ctr"] == expected_ctr
    
    # Проверяем расчёт CPC
    expected_cpc = round((result["spend"] / result["clicks"]), 2)
    assert result["cpc"] == expected_cpc
    
    # Проверяем расчёт CPA
    expected_cpa = round((result["spend"] / result["conversions"]), 2)
    assert result["cpa"] == expected_cpa


def test_kpi_summary_empty_data(session: Session, org_a: Organization, connection_yandex: Connection):
    """Тест сводки KPI при отсутствии данных"""
    today = date.today()
    result = build_kpi_summary(
        db=session,
        org_id=org_a.id,
        date_from=today - timedelta(days=5),
        date_to=today,
        connection_ids=[connection_yandex.id],
        platform=None
    )
    
    assert result["impressions"] == 0
    assert result["clicks"] == 0
    assert result["conversions"] == 0
    assert result["spend"] == 0
    assert result["ctr"] is None
    assert result["cpc"] is None
    assert result["cpa"] is None


def test_kpi_timeseries_org_scoping(session: Session, org_a: Organization):
    """Тест org scoping - запрос с чужими connection_ids должен вернуть 404"""
    from app.db.models import Organization
    from fastapi import HTTPException
    
    org_b = Organization(name="Org B")
    session.add(org_b)
    session.commit()
    session.refresh(org_b)
    
    conn_org_b = Connection(
        organization_id=org_b.id,
        name="Org B Connection",
        platform=Platform.yandex,
        credentials_json={}
    )
    session.add(conn_org_b)
    session.commit()
    session.refresh(conn_org_b)
    
    # Попытка запросить данные org_b через org_a должна вызвать 404
    today = date.today()
    with pytest.raises(HTTPException) as exc_info:
        build_kpi_timeseries(
            db=session,
            org_id=org_a.id,
            date_from=today - timedelta(days=5),
            date_to=today,
            connection_ids=[conn_org_b.id],  # connection из другой org
            platform=None,
            mode="index"
        )
    
    assert exc_info.value.status_code == 404


def test_kpi_summary_org_scoping(session: Session, org_a: Organization):
    """Тест org scoping для summary"""
    from app.db.models import Organization
    from fastapi import HTTPException
    
    org_b = Organization(name="Org B")
    session.add(org_b)
    session.commit()
    session.refresh(org_b)
    
    conn_org_b = Connection(
        organization_id=org_b.id,
        name="Org B Connection",
        platform=Platform.yandex,
        credentials_json={}
    )
    session.add(conn_org_b)
    session.commit()
    session.refresh(conn_org_b)
    
    today = date.today()
    with pytest.raises(HTTPException) as exc_info:
        build_kpi_summary(
            db=session,
            org_id=org_a.id,
            date_from=today - timedelta(days=5),
            date_to=today,
            connection_ids=[conn_org_b.id],
            platform=None
        )
    
    assert exc_info.value.status_code == 404
