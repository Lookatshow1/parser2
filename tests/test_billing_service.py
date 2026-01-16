import pytest
from unittest.mock import MagicMock
from decimal import Decimal
from app.services.billing import BillingService
from app.db.models_billing import BillingAccount, BillingTransaction, BillingDocument


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    return db


@pytest.fixture
def billing_service(mock_db):
    """Create BillingService instance with mock DB."""
    return BillingService(mock_db)


class TestBillingService:
    
    def test_get_or_create_account_existing(self, billing_service, mock_db):
        """Test returns existing account if found."""
        existing_account = BillingAccount(id=1, organization_id=1, balance=100.0, reserved_balance=0, currency="RUB")
        mock_db.query.return_value.filter.return_value.first.return_value = existing_account
        
        result = billing_service.get_or_create_account(1)
        
        assert result == existing_account
        mock_db.add.assert_not_called()


    def test_get_or_create_account_new(self, billing_service, mock_db):
        """Test creates new account if not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = billing_service.get_or_create_account(1)
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # Check the created account
        added_account = mock_db.add.call_args[0][0]
        assert added_account.organization_id == 1
        assert added_account.balance == 0.0


    def test_process_topup(self, billing_service, mock_db):
        """Test topup increases balance and creates transaction."""
        existing_account = BillingAccount(id=1, organization_id=1, balance=100.0, reserved_balance=0, currency="RUB")
        mock_db.query.return_value.filter.return_value.first.return_value = existing_account
        
        result = billing_service.process_topup(1, 50.0)
        
        # Balance should increase
        assert existing_account.balance == 150.0
        
        # Transaction should be created
        assert mock_db.add.call_count == 1
        added_tx = mock_db.add.call_args[0][0]
        assert isinstance(added_tx, BillingTransaction)
        assert added_tx.type == "topup"
        assert added_tx.amount == 50.0


    def test_generate_invoice(self, billing_service, mock_db):
        """Test invoice generation creates document."""
        existing_account = BillingAccount(id=1, organization_id=1, balance=100.0, reserved_balance=0, currency="RUB")
        mock_db.query.return_value.filter.return_value.first.return_value = existing_account
        
        doc = billing_service.generate_invoice(1, 200.0)
        
        mock_db.add.assert_called_once()
        added_doc = mock_db.add.call_args[0][0]
        assert added_doc.type == "invoice"
        assert "INV-" in added_doc.number
