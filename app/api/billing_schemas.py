from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class BillingAccountResponse(BaseModel):
    id: int
    organization_id: int
    balance: float
    status: str = "active"
    class Config:
        from_attributes = True

class TransactionResponse(BaseModel):
    id: int
    type: str # credit, debit
    amount: float
    status: str
    description: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class TopupRequest(BaseModel):
    amount: float

class InvoiceRequest(BaseModel):
    amount: float
