from sqlalchemy.orm import Session
from app.db.models_billing import BillingAccount, BillingTransaction, BillingDocument
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
                reserved_balance=0.0,
                currency="RUB"
            )
            self.db.add(account)
            self.db.commit()
            self.db.refresh(account)
        return account

    def process_topup(self, org_id: int, amount: float, description: str = "Manual Topup"):
        account = self.get_or_create_account(org_id)
        
        # Create Transaction with correct model fields
        tx = BillingTransaction(
            organization_id=org_id,
            type="topup",
            amount=amount,
            status="succeeded",
            provider="mock",
            external_id=str(uuid.uuid4()),
            meta_json={"description": description}
        )
        self.db.add(tx)
        
        # Update Balance
        account.balance += amount
        self.db.commit()
        
        return account

    def generate_invoice(self, org_id: int, amount: float) -> BillingDocument:
        self.get_or_create_account(org_id)
        
        doc = BillingDocument(
            organization_id=org_id,
            type="invoice",
            status="draft",
            number=f"INV-{int(datetime.utcnow().timestamp())}",
            meta_json={"amount": amount, "url": f"https://mock-docs.example.com/inv-{org_id}-{int(amount)}.pdf"}
        )
        self.db.add(doc)
        self.db.commit()
        return doc
