from typing import Dict, Type
from app.adapters.platforms.base import PlatformAdapter
from app.adapters.platforms.yandex_mock import YandexMockAdapter
from app.db.models_drafts import DraftCampaign
from app.db.models import Connection, OrgUtmSettings, Platform
from sqlalchemy.orm import Session
from datetime import datetime
from app.utils.utm import build_utm_from_org_settings, build_utm_url
from app.security.credentials_crypto import maybe_decrypt
from app.services.campaign_publisher import CampaignPublisher
from app.services.oauth.base import OzonOAuth

class IntegrationService:
    def __init__(self, db: Session):
        self.db = db
        self._adapters: Dict[str, Type[PlatformAdapter]] = {
            "yandex": YandexMockAdapter,
            # "google": GoogleAdWordsAdapter, # Future
        }

    def get_adapter(self, platform: str) -> PlatformAdapter:
        adapter_cls = self._adapters.get(platform.lower())
        if not adapter_cls:
            raise ValueError(f"Platform {platform} not supported")
        return adapter_cls()

    async def publish_draft(self, draft_id: int):
        draft = self.db.query(DraftCampaign).filter(DraftCampaign.id == draft_id).first()
        if not draft:
            raise ValueError("Draft not found")

        if draft.connection_id:
            connection = (
                self.db.query(Connection)
                .filter(Connection.id == draft.connection_id)
                .first()
            )
            if not connection:
                raise ValueError("Connection not found for draft")

            token = await self._resolve_connection_token(connection)
            publisher = CampaignPublisher(self.db)
            result = await publisher.publish(draft.id, token)
            if not result.success:
                raise ValueError(result.error or "Publish failed")
            return result.external_id or result.campaign_id or ""

        adapter = self.get_adapter(draft.platform)

        # Apply UTM tags to all ads
        self._apply_utms(draft)

        # In a real system, we'd recursively convert DraftAdGroups -> Platform Format
        # Here we just mock the campaign creation call
        external_id = await adapter.publish_campaign(draft)

        draft.status = "published"
        draft.payload_json = {**(draft.payload_json or {}), "external_id": external_id}
        draft.updated_at = datetime.utcnow()
        self.db.commit()

        return external_id

    async def _resolve_connection_token(self, connection: Connection) -> str:
        creds = maybe_decrypt(connection.credentials_json or {})
        if connection.platform == Platform.yandex:
            token = creds.get("token") or creds.get("access_token")
            if not token:
                raise ValueError("Yandex token is missing")
            return token
        if connection.platform == Platform.vk:
            token = creds.get("access_token") or creds.get("token")
            if not token:
                raise ValueError("VK access token is missing")
            return token
        if connection.platform == Platform.ozon:
            if creds.get("access_token"):
                return creds["access_token"]
            client_id = creds.get("client_id")
            client_secret = creds.get("client_secret")
            if not client_id or not client_secret:
                raise ValueError("Ozon credentials are missing")
            oauth = OzonOAuth(client_id=client_id, client_secret=client_secret, redirect_uri="")
            token = await oauth.exchange_code("")
            await oauth.close()
            return token.access_token
        raise ValueError(f"Unsupported platform: {connection.platform}")

    def _apply_utms(self, campaign: DraftCampaign):
        settings = (
            self.db.query(OrgUtmSettings)
            .filter(OrgUtmSettings.organization_id == campaign.organization_id)
            .first()
        )
        try:
            platform = Platform(campaign.platform)
        except ValueError:
            platform = None

        for group in campaign.ad_groups:
            for ad in group.ads:
                if not ad.landing_url:
                    continue

                if isinstance(settings, OrgUtmSettings) and platform:
                    ad.final_url = build_utm_from_org_settings(
                        base_url=ad.landing_url,
                        org_settings=settings,
                        platform=platform,
                        campaign_id=str(campaign.id),
                        ad_group_id=str(group.id),
                        ad_id=str(ad.id),
                    )
                else:
                    params = {
                        "utm_source": campaign.platform,
                        "utm_medium": "cpc",
                        "utm_campaign": str(campaign.id),
                        "utm_content": str(ad.id),
                    }
                    ad.final_url = build_utm_url(ad.landing_url, params)


    async def import_campaigns_to_drafts(self, platform: str, account_id: str, org_id: int):
        adapter = self.get_adapter(platform)
        campaigns_data = await adapter.fetch_campaigns(account_id)
        
        created_drafts = []
        for c_data in campaigns_data:
            # Create a draft from the imported data
            draft = DraftCampaign(
                organization_id=org_id,
                name=f"[Import] {c_data['name']}",
                platform=platform,
                status="draft",
                payload_json=c_data
            )
            self.db.add(draft)
            self.db.commit()
            created_drafts.append(draft)
            
        return created_drafts

    async def import_campaigns(self, platform: str, account_id: str, org_id: int):
        adapter = self.get_adapter(platform)
        campaigns_data = await adapter.fetch_campaigns(account_id)
        
        created_drafts = []
        for c_data in campaigns_data:
            draft = DraftCampaign(
                organization_id=org_id,
                name=f"[Import] {c_data['name']}",
                platform=platform,
                status="draft",
                payload_json=c_data
            )
            self.db.add(draft)
            self.db.commit()
            created_drafts.append(draft)
            
        return created_drafts
