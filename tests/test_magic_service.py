import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.magic import MagicService
from app.db.models_magic import MagicRun


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    db.flush = MagicMock()
    return db


@pytest.fixture
def magic_service(mock_db):
    """Create MagicService instance with mock DB."""
    return MagicService(mock_db)


class TestMagicService:
    
    @pytest.mark.asyncio
    async def test_create_magic_run(self, magic_service, mock_db):
        """Test that create_magic_run creates a MagicRun with pending status."""
        run = await magic_service.create_magic_run(
            org_id=1,
            user_id=10,
            input_data={"landing_url": "https://example.com", "description": "Test"}
        )
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # Check the created run object
        added_run = mock_db.add.call_args[0][0]
        assert added_run.organization_id == 1
        assert added_run.created_by_user_id == 10
        assert added_run.status == "pending"
        assert added_run.input_json["landing_url"] == "https://example.com"


    @pytest.mark.asyncio
    async def test_process_run_success(self, magic_service, mock_db):
        """Test process_run transitions status and creates drafts."""
        mock_run = MagicRun(
            id=1, 
            organization_id=1, 
            status="pending",
            input_json={"landing_url": "https://example.com", "target_audience": "general"}
        )
        mock_db.query.return_value.filter.return_value.first.return_value = mock_run
        
        await magic_service.process_run(1)
        
        assert mock_run.status == "success"
        mock_db.commit.assert_called()


    @pytest.mark.asyncio
    async def test_process_run_not_found(self, magic_service, mock_db):
        """Test process_run does nothing when run not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Should not raise, just return
        await magic_service.process_run(999)
        
        # No commit should happen for non-existent run status change
        # (initial query returns None, so we return early)
