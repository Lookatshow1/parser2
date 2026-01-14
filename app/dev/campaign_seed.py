from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import Campaign, CampaignAdGroup, CampaignAd, CampaignEvent, CampaignStatus, Organization, User, Platform


def seed_campaigns(session: Session, org: Organization, user: User) -> dict:
    campaign = (
        session.query(Campaign)
        .filter(Campaign.organization_id == org.id, Campaign.name == "Демо-кампания")
        .first()
    )
    if campaign is None:
        campaign = Campaign(
            organization_id=org.id,
            platform=Platform.yandex,
            name="Демо-кампания",
            objective="Рост заявок",
            status=CampaignStatus.draft,
            budget_total=150000,
            budget_daily=5000,
            created_by_user_id=user.id,
        )
        session.add(campaign)
        session.flush()
        session.add(
            CampaignEvent(
                organization_id=org.id,
                entity_type="campaign",
                entity_id=campaign.id,
                action="created",
                payload_json={"name": campaign.name},
                created_by_user_id=user.id,
            )
        )

    def ensure_group(name: str, status: CampaignStatus) -> CampaignAdGroup:
        group = (
            session.query(CampaignAdGroup)
            .filter(CampaignAdGroup.campaign_id == campaign.id, CampaignAdGroup.name == name)
            .first()
        )
        if group is None:
            group = CampaignAdGroup(
                campaign_id=campaign.id,
                name=name,
                status=status,
                bid_strategy="maximize_conversions",
                budget_daily=2500,
                targeting_json={"geo": ["Москва"], "age": [25, 45]},
            )
            session.add(group)
            session.flush()
            session.add(
                CampaignEvent(
                    organization_id=org.id,
                    entity_type="ad_group",
                    entity_id=group.id,
                    action="created",
                    payload_json={"campaign_id": campaign.id},
                    created_by_user_id=user.id,
                )
            )
        return group

    group_a = ensure_group("Группа 1", CampaignStatus.draft)
    group_b = ensure_group("Группа 2", CampaignStatus.active)

    def ensure_ad(group: CampaignAdGroup, name: str, status: CampaignStatus, title: str) -> None:
        ad = (
            session.query(CampaignAd)
            .filter(CampaignAd.ad_group_id == group.id, CampaignAd.name == name)
            .first()
        )
        if ad is None:
            ad = CampaignAd(
                ad_group_id=group.id,
                name=name,
                status=status,
                landing_url="https://example.com",
                creative_json={
                    "title": title,
                    "text": "Лучшие условия для вашей рекламы",
                    "image_url": "",
                    "call_to_action": "Перейти",
                },
            )
            session.add(ad)
            session.flush()
            session.add(
                CampaignEvent(
                    organization_id=org.id,
                    entity_type="ad",
                    entity_id=ad.id,
                    action="created",
                    payload_json={"ad_group_id": group.id},
                    created_by_user_id=user.id,
                )
            )

    ensure_ad(group_a, "Объявление 1", CampaignStatus.draft, "Больше заявок за неделю")
    ensure_ad(group_a, "Объявление 2", CampaignStatus.paused, "Сезонная акция")
    ensure_ad(group_b, "Объявление 3", CampaignStatus.active, "Рост продаж без риска")

    session.commit()

    return {
        "campaign_id": campaign.id,
        "group_ids": [group_a.id, group_b.id],
    }
