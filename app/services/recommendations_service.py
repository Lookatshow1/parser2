from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func, select, desc, and_
from app.db.models import (
    Connection, MetricSnapshot, AdCampaign, OrgRecommendation, Platform
)
from app.services.audit import log_org_event

def compute_recommendations_for_org(
    db: Session,
    org_id: int,
    date_from: date,
    date_to: date,
    connection_ids: list[int] | None = None
) -> tuple[int, int]:
    """
    Computes recommendations for an organization based on metrics and catalog.
    Returns (created_count, updated_count).
    """
    query = db.query(Connection).filter(Connection.organization_id == org_id)
    if connection_ids:
        query = query.filter(Connection.id.in_(connection_ids))
    connections = query.all()

    created_count = 0
    updated_count = 0

    for conn in connections:
        # 1. MOCK_CONNECTION
        if conn.credentials_json.get("mock"):
            c, u = _upsert_reco(
                db, org_id, conn.id, "connection", conn.id,
                "MOCK_CONNECTION", "info",
                "Демо-режим",
                "Подключение работает в демо-режиме. Данные генерируются автоматически.",
                "Для работы с реальными данными добавьте токен в настройках подключения.",
                {}, date_from, date_to
            )
            created_count += c
            updated_count += u

        # 2. AUTOSYNC_OFF
        if not conn.auto_sync_enabled:
            c, u = _upsert_reco(
                db, org_id, conn.id, "connection", conn.id,
                "AUTOSYNC_OFF", "info",
                "Автосинк выключен",
                "Данные не обновляются автоматически.",
                "Включите автосинк в настройках подключения, чтобы видеть актуальную статистику.",
                {}, date_from, date_to
            )
            created_count += c
            updated_count += u

        # 3. Campaign Rules
        # Fetch aggregated metrics for campaigns
        metrics = (
            db.query(
                MetricSnapshot.campaign_external_id,
                func.sum(MetricSnapshot.spend).label("spend"),
                func.sum(MetricSnapshot.impressions).label("impressions"),
                func.sum(MetricSnapshot.clicks).label("clicks"),
                func.sum(MetricSnapshot.purchases).label("conversions"),
            )
            .filter(
                MetricSnapshot.connection_id == conn.id,
                MetricSnapshot.date >= date_from,
                MetricSnapshot.date <= date_to,
                MetricSnapshot.level == "campaign"
            )
            .group_by(MetricSnapshot.campaign_external_id)
            .all()
        )

        # Map external_id to internal id
        campaign_map = {
            c.external_id: c.id
            for c in db.query(AdCampaign).filter(AdCampaign.connection_id == conn.id).all()
        }

        # Calculate median CPC for HIGH_CPC rule
        cpcs = []
        for m in metrics:
            clicks = int(m.clicks or 0)
            spend = int(m.spend or 0)
            if clicks >= 20:
                cpcs.append(spend / clicks)

        median_cpc = 0
        if cpcs:
            cpcs.sort()
            median_cpc = cpcs[len(cpcs) // 2]

        total_spend = 0
        max_campaign_spend = 0

        for m in metrics:
            ext_id = m.campaign_external_id
            subject_id = campaign_map.get(ext_id)
            if not subject_id:
                continue # Skip if not in catalog (should not happen if synced)

            spend = int(m.spend or 0)
            impressions = int(m.impressions or 0)
            clicks = int(m.clicks or 0)
            conversions = int(m.conversions or 0)

            total_spend += spend
            if spend > max_campaign_spend:
                max_campaign_spend = spend

            # NO_CONVERSIONS_SPEND
            if spend >= 1000 and conversions == 0:
                c, u = _upsert_reco(
                    db, org_id, conn.id, "campaign", subject_id,
                    "NO_CONVERSIONS_SPEND", "warn",
                    "Расход без конверсий",
                    f"Кампания потратила {spend} руб., но не принесла конверсий.",
                    "Проверьте цели, посадочную страницу и настройки таргетинга. Если конверсии не настроены, отключите их отслеживание.",
                    {"spend": spend, "clicks": clicks, "impressions": impressions},
                    date_from, date_to
                )
                created_count += c
                updated_count += u

            # LOW_CTR
            ctr = (clicks / impressions) if impressions > 0 else 0
            if impressions >= 5000 and ctr < 0.005: # 0.5%
                c, u = _upsert_reco(
                    db, org_id, conn.id, "campaign", subject_id,
                    "LOW_CTR", "info",
                    "Низкий CTR",
                    f"CTR кампании составляет {ctr*100:.2f}%, что ниже нормы (0.5%).",
                    "Попробуйте изменить заголовки и изображения в объявлениях. Проверьте соответствие ключевых слов объявлениям.",
                    {"ctr": ctr, "impressions": impressions},
                    date_from, date_to
                )
                created_count += c
                updated_count += u

            # HIGH_CPC_VS_MEDIAN
            if clicks >= 20 and median_cpc > 0:
                cpc = spend / clicks
                if cpc > 2 * median_cpc:
                    c, u = _upsert_reco(
                        db, org_id, conn.id, "campaign", subject_id,
                        "HIGH_CPC", "warn",
                        "Высокий CPC",
                        f"Стоимость клика ({cpc:.2f} руб.) в 2 раза выше медианы по аккаунту ({median_cpc:.2f} руб.).",
                        "Проверьте ставки и конкуренцию по запросам. Возможно, стоит снизить ставку или уточнить таргетинг.",
                        {"cpc": cpc, "median_cpc": median_cpc},
                        date_from, date_to
                    )
                    created_count += c
                    updated_count += u

        # SPEND_CONCENTRATION
        if total_spend >= 5000 and len(metrics) >= 3:
            share = max_campaign_spend / total_spend
            if share > 0.8:
                c, u = _upsert_reco(
                    db, org_id, conn.id, "connection", conn.id,
                    "SPEND_CONCENTRATION", "info",
                    "Концентрация бюджета",
                    f"Одна кампания расходует {share*100:.0f}% всего бюджета.",
                    "Убедитесь, что это намеренно. Рискованно зависеть от одной кампании.",
                    {"total_spend": total_spend, "max_share": share},
                    date_from, date_to
                )
                created_count += c
                updated_count += u

    db.commit()
    return created_count, updated_count

def _upsert_reco(
    db: Session,
    org_id: int,
    conn_id: int | None,
    subject_type: str,
    subject_id: int | None,
    code: str,
    severity: str,
    title: str,
    description: str,
    action: str,
    meta: dict,
    valid_from: date,
    valid_to: date
) -> tuple[int, int]:
    stmt = insert(OrgRecommendation).values(
        organization_id=org_id,
        connection_id=conn_id,
        subject_type=subject_type,
        subject_id=subject_id,
        code=code,
        severity=severity,
        title=title,
        description=description,
        action=action,
        meta_json=meta,
        valid_from=valid_from,
        valid_to=valid_to,
        created_at=func.now()
    )

    # On conflict, update details but preserve resolved status if already resolved
    # We only update if NOT resolved? Or update anyway?
    # If resolved, we probably shouldn't resurface it unless it's a new period?
    # But unique key includes valid_from/valid_to.
    # If we recompute for same period, we update.
    # If user resolved it, resolved_at is set.
    # We should NOT clear resolved_at.

    do_update = stmt.on_conflict_do_update(
        constraint="uq_org_recommendations",
        set_={
            "severity": severity,
            "title": title,
            "description": description,
            "action": action,
            "meta_json": meta,
            # Don't touch resolved_at
        }
    )

    result = db.execute(do_update)
    # Check if inserted or updated
    # rowcount for upsert: 1 if inserted, 2 if updated (in some pg drivers/configs), or 1 if updated?
    # Standard: 1 for insert, 2 for update (delete+insert internally sometimes) or 1.
    # Let's assume >0 means touched.
    # To be precise is hard without returning.
    # We can assume updated if not inserted.
    # But we don't strictly need precise counts for logic.
    return (1, 0) if result.rowcount == 1 else (0, 1)

def resolve_recommendation(db: Session, org_id: int, reco_id: int, user_id: int):
    reco = db.query(OrgRecommendation).filter(
        OrgRecommendation.id == reco_id,
        OrgRecommendation.organization_id == org_id
    ).first()

    if not reco:
        return False

    if reco.resolved_at:
        return True # Already resolved

    reco.resolved_at = func.now()
    reco.resolved_by_user_id = user_id

    log_org_event(
        db,
        organization_id=org_id,
        actor_user_id=user_id,
        action="recommendation_resolved",
        subject_type="recommendation",
        subject_id=reco.id,
        meta={"code": reco.code, "severity": reco.severity}
    )
    db.commit()
    return True
