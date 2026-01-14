from sqlalchemy.orm import Session

from app.db.models import Campaign, CampaignAdGroup, CampaignAd, CampaignEvent, CampaignStatus


def cascade_campaign_status(
    db: Session,
    campaign: Campaign,
    status: CampaignStatus,
    action: str,
    user_id: int | None,
) -> Campaign:
    campaign.status = status
    groups = db.query(CampaignAdGroup).filter(CampaignAdGroup.campaign_id == campaign.id).all()
    for group in groups:
        group.status = status
        ads = db.query(CampaignAd).filter(CampaignAd.ad_group_id == group.id).all()
        for ad in ads:
            ad.status = status
    db.add(
        CampaignEvent(
            organization_id=campaign.organization_id,
            entity_type="campaign",
            entity_id=campaign.id,
            action=action,
            payload_json={},
            created_by_user_id=user_id,
        )
    )
    return campaign
