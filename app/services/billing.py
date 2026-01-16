from sqlalchemy.orm import Session
from app.db.models_billing import BillingAccount, BillingTransaction, BillingDocument
from app.db.models import Organization
import uuid
from datetime import datetime

class BillingService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_account(self, org_id: int) -> BillingAccount:
        account = self.db.query(BillingAccount).filter(BillingAccount.organization_id == org_id).first()
        if not account:
            account = BillingAccount(
                organization_id=org_id,
                balance=0.0,
                status="active"
            )
            self.db.add(account)
            self.db.commit()
            self.db.refresh(account)
        return account

    def process_topup(self, org_id: int, amount: float, description: str = "Manual Topup"):
        account = self.get_or_create_account(org_id)
        
        # Create Transaction
        tx = BillingTransaction(
            account_id=account.id,
            type="credit",
            amount=amount,
            status="success",
            description=description,
            reference_id=str(uuid.uuid4())
        )
        self.db.add(tx)
        
        # Update Balance
        account.balance += amount
        account.updated_at = datetime.utcnow()
        self.db.commit()
        
        return account

    def generate_invoice(self, org_id: int, amount: float) -> BillingDocument:
        account = self.get_or_create_account(org_id)
        
        doc = BillingDocument(
            account_id=account.id,
            type="invoice",
            status="pending",
            document_number=f"INV-{int(datetime.utcnow().timestamp())}",
            amount=amount,
            url=f"https://mock-docs.example.com/inv-{org_id}-{int(amount)}.pdf" # Mock URL
        )
        self.db.add(doc)
        self.db.commit()
        return doc
