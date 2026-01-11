import pytest
from datetime import date, timedelta
from app.services.dashboard_unified_service import get_unified_timeseries, get_dashboard_channels
from app.db.models import Platform

def test_unified_timeseries_basic(session, org_a, connection_yandex, metric_snapshot_factory):
    # Setup data
    d1 = date.today()
    metric_snapshot_factory(
        connection=connection_yandex,
        date=d1,
        clicks=100,
        impressions=1000,
        purchases=5,
        spend=500
    )

    # Call service
    res = get_unified_timeseries(session, org_a.id, d1, d1)

    assert len(res["series"]) == 1
    point = res["series"][0]
    assert point["date"] == d1
    assert point["raw"]["clicks"] == 100
    assert point["norm"]["clicks"] == 1.0 # Max for period
    assert point["index"] == 1.0 # Average of 1.0s

    assert res["totals"]["clicks"] == 100
    assert res["kpi"]["ctr"] == 0.1

def test_unified_timeseries_channels(session, org_a, connection_yandex):
    ch = get_dashboard_channels(session, org_a.id)
    assert len(ch) >= 2 # All + Yandex
    assert ch[0]["key"] == "all"
    assert ch[1]["key"] == "yandex"

def test_unified_timeseries_scoping(session, org_b, connection_yandex, metric_snapshot_factory):
    # Data in org_a
    metric_snapshot_factory(connection=connection_yandex, clicks=100)

    # Query org_b
    res = get_unified_timeseries(session, org_b.id, date.today(), date.today())
    assert len(res["series"]) == 0
    assert res["totals"]["clicks"] == 0

def test_normalization(session, org_a, connection_yandex, metric_snapshot_factory):
    d1 = date.today()
    d2 = d1 + timedelta(days=1)

    # Day 1: 100 clicks
    metric_snapshot_factory(connection=connection_yandex, date=d1, clicks=100, spend=0, impressions=0, purchases=0)
    # Day 2: 50 clicks
    metric_snapshot_factory(connection=connection_yandex, date=d2, clicks=50, spend=0, impressions=0, purchases=0)

    res = get_unified_timeseries(session, org_a.id, d1, d2)
    assert len(res["series"]) == 2

    # Day 1 should be 1.0 (max)
    p1 = next(p for p in res["series"] if p["date"] == d1)
    assert p1["norm"]["clicks"] == 1.0

    # Day 2 should be 0.5
    p2 = next(p for p in res["series"] if p["date"] == d2)
    assert p2["norm"]["clicks"] == 0.5
