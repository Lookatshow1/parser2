from app.db.models import Campaign, CampaignAdGroup, CampaignAd, CampaignStatus, Platform, Organization, User
from app.services.campaign_service import cascade_campaign_status
from app.services.auth_service import get_password_hash


def test_cascade_campaign_status(db_session):
    org = Organization(name="Org Campaign")
    db_session.add(org)
    db_session.commit()
    user = User(email="owner@example.com", password_hash=get_password_hash("pass"), is_active=True, active_organization_id=org.id)
    db_session.add(user)
    db_session.commit()

    campaign = Campaign(
        organization_id=org.id,
        platform=Platform.yandex,
        name="Test Campaign",
        status=CampaignStatus.draft,
        created_by_user_id=user.id,
    )
    db_session.add(campaign)
    db_session.commit()

    group = CampaignAdGroup(campaign_id=campaign.id, name="Group A", status=CampaignStatus.draft, targeting_json={})
    db_session.add(group)
    db_session.commit()

    ad = CampaignAd(ad_group_id=group.id, name="Ad 1", status=CampaignStatus.draft, creative_json={})
    db_session.add(ad)
    db_session.commit()

    cascade_campaign_status(db_session, campaign, CampaignStatus.active, "published", user.id)
    db_session.commit()
    db_session.refresh(campaign)
    db_session.refresh(group)
    db_session.refresh(ad)

    assert campaign.status == CampaignStatus.active
    assert group.status == CampaignStatus.active
    assert ad.status == CampaignStatus.active
