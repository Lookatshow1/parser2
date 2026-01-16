import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.integrations import IntegrationService
from app.db.models_drafts import DraftCampaign, DraftAdGroup, DraftAd


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    return db


@pytest.fixture
def integration_service(mock_db):
    """Create IntegrationService instance with mock DB."""
    return IntegrationService(mock_db)


class TestIntegrationService:
    
    def test_get_adapter_yandex(self, integration_service):
        """Test Yandex adapter is returned."""
        from app.adapters.platforms.yandex_mock import YandexMockAdapter
        
        adapter = integration_service.get_adapter("yandex")
        
        assert isinstance(adapter, YandexMockAdapter)


    def test_get_adapter_invalid(self, integration_service):
        """Test ValueError for unsupported platform."""
        with pytest.raises(ValueError, match="not supported"):
            integration_service.get_adapter("tiktok")


    @pytest.mark.asyncio
    async def test_publish_draft_success(self, integration_service, mock_db):
        """Test publish_draft updates status and returns external ID."""
        mock_draft = DraftCampaign(
            id=1,
            organization_id=1,
            name="Test Campaign",
            platform="yandex",
            status="draft",
            payload_json={},
            ad_groups=[]
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_draft
        
        external_id = await integration_service.publish_draft(1)
        
        assert external_id.startswith("ya_new_")
        assert mock_draft.status == "published"
        assert mock_draft.payload_json.get("external_id") == external_id


    @pytest.mark.asyncio
    async def test_publish_draft_not_found(self, integration_service, mock_db):
        """Test publish_draft raises error when draft not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="Draft not found"):
            await integration_service.publish_draft(999)


    @pytest.mark.asyncio
    async def test_import_campaigns(self, integration_service, mock_db):
        """Test import_campaigns creates drafts from platform data."""
        drafts = await integration_service.import_campaigns("yandex", "acc123", 1)
        
        # YandexMockAdapter returns 2 campaigns
        assert mock_db.add.call_count == 2
        assert mock_db.commit.call_count == 2


    def test_apply_utms(self, integration_service):
        """Test UTM parameters are correctly applied to ads."""
        mock_ad = DraftAd(
            id=10,
            ad_group_id=5,
            landing_url="https://example.com/landing?existing=param"
        )
        mock_group = DraftAdGroup(id=5, campaign_id=1, name="Group", ads=[mock_ad])
        mock_campaign = DraftCampaign(
            id=1,
            organization_id=1,
            name="Test Campaign",
            platform="yandex",
            ad_groups=[mock_group]
        )
        
        integration_service._apply_utms(mock_campaign)
        
        assert mock_ad.final_url is not None
        assert "utm_source=yandex" in mock_ad.final_url
        assert "utm_medium=cpc" in mock_ad.final_url
        assert "utm_campaign=1-" in mock_ad.final_url
        assert "utm_content=10" in mock_ad.final_url
        assert "existing=param" in mock_ad.final_url
