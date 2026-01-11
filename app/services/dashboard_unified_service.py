from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func, select
from app.db.models import MetricSnapshot, Connection, Platform

def get_dashboard_channels(db: Session, org_id: int) -> list[dict]:
    # Get unique platforms from connections
    platforms = db.execute(
        select(Connection.platform).where(Connection.organization_id == org_id).distinct()
    ).scalars().all()

    channels = [{"key": "all", "title": "Все каналы"}]

    platform_titles = {
        Platform.yandex: "Яндекс Директ",
        Platform.vk: "VK Реклама",
        Platform.ozon: "Ozon",
        Platform.stub: "Демо канал"
    }

    for p in platforms:
        channels.append({"key": p.value, "title": platform_titles.get(p, p.value)})

    return channels

def get_unified_timeseries(
    db: Session,
    org_id: int,
    date_from: date,
    date_to: date,
    channel: str = "all",
    connection_ids: list[int] | None = None
) -> dict:
    # 1. Filter connections
    conn_query = select(Connection.id).where(Connection.organization_id == org_id)
    if channel != "all":
        conn_query = conn_query.where(Connection.platform == channel)
    if connection_ids:
        conn_query = conn_query.where(Connection.id.in_(connection_ids))

    valid_conn_ids = db.execute(conn_query).scalars().all()

    if not valid_conn_ids:
        return {
            "date_from": date_from,
            "date_to": date_to,
            "channel": channel,
            "available_channels": get_dashboard_channels(db, org_id),
            "series": [],
            "totals": {"clicks": 0, "impressions": 0, "conversions": 0, "spend": 0},
            "kpi": {"ctr": None, "cpc": None, "cpm": None, "cpa": None, "roas": None}
        }

    # 2. Aggregate metrics by date
    # We sum up campaign level snapshots to avoid double counting if ad_group level exists
    # Or just sum everything and assume snapshots are consistent.
    # Safer to filter level='campaign' as it's the base.

    rows = db.execute(
        select(
            MetricSnapshot.date,
            func.sum(MetricSnapshot.clicks).label("clicks"),
            func.sum(MetricSnapshot.impressions).label("impressions"),
            func.sum(MetricSnapshot.purchases).label("conversions"), # purchases as conversions
            func.sum(MetricSnapshot.spend).label("spend"),
            func.sum(MetricSnapshot.revenue).label("revenue")
        )
        .where(
            MetricSnapshot.organization_id == org_id,
            MetricSnapshot.connection_id.in_(valid_conn_ids),
            MetricSnapshot.date >= date_from,
            MetricSnapshot.date <= date_to,
            MetricSnapshot.level == "campaign"
        )
        .group_by(MetricSnapshot.date)
        .order_by(MetricSnapshot.date)
    ).all()

    # 3. Process data
    series = []
    totals = {"clicks": 0, "impressions": 0, "conversions": 0, "spend": 0, "revenue": 0}

    # Find max for normalization
    max_vals = {"clicks": 0, "impressions": 0, "conversions": 0, "spend": 0}

    temp_data = []
    for r in rows:
        d = {
            "date": r.date,
            "clicks": int(r.clicks or 0),
            "impressions": int(r.impressions or 0),
            "conversions": int(r.conversions or 0),
            "spend": int(r.spend or 0),
            "revenue": int(r.revenue or 0)
        }
        temp_data.append(d)

        totals["clicks"] += d["clicks"]
        totals["impressions"] += d["impressions"]
        totals["conversions"] += d["conversions"]
        totals["spend"] += d["spend"]
        totals["revenue"] += d["revenue"]

        max_vals["clicks"] = max(max_vals["clicks"], d["clicks"])
        max_vals["impressions"] = max(max_vals["impressions"], d["impressions"])
        max_vals["conversions"] = max(max_vals["conversions"], d["conversions"])
        max_vals["spend"] = max(max_vals["spend"], d["spend"])

    # 4. Normalize and Index
    for d in temp_data:
        norm = {}
        for k in ["clicks", "impressions", "conversions", "spend"]:
            m = max_vals[k]
            norm[k] = d[k] / m if m > 0 else 0.0

        # Index = average of norms (simple version)
        # We can use weights later
        idx = (norm["clicks"] + norm["impressions"] + norm["conversions"] + norm["spend"]) / 4.0

        series.append({
            "date": d["date"],
            "raw": {k: d[k] for k in ["clicks", "impressions", "conversions", "spend"]},
            "norm": norm,
            "index": round(idx, 4)
        })

    # 5. KPI
    def safe_div(a, b): return a / b if b > 0 else None

    kpi = {
        "ctr": safe_div(totals["clicks"], totals["impressions"]),
        "cpc": safe_div(totals["spend"], totals["clicks"]),
        "cpm": safe_div(totals["spend"] * 1000, totals["impressions"]),
        "cpa": safe_div(totals["spend"], totals["conversions"]),
        "roas": safe_div(totals["revenue"], totals["spend"])
    }

    return {
        "date_from": date_from,
        "date_to": date_to,
        "channel": channel,
        "available_channels": get_dashboard_channels(db, org_id),
        "series": series,
        "totals": {k: v for k, v in totals.items() if k != "revenue"}, # revenue not in schema totals but used for KPI
        "kpi": kpi
    }
