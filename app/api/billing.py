from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db, get_current_user
from app.db.models import User
from app.services.billing import BillingService
from app.api.billing_schemas import BillingAccountResponse, TransactionResponse, TopupRequest, InvoiceRequest

router = APIRouter(prefix="/billing", tags=["Billing"])

@router.get("/balance", response_model=BillingAccountResponse)
def get_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Determine Org ID (Mock logic: generic or user's first)
    # Real logic should check X-Org-ID header or similar context
    service = BillingService(db)
    # Mocking Org ID as 1 for simplicity if not in context
    org_id = 1 
    return service.get_or_create_account(org_id)

@router.post("/topup", response_model=BillingAccountResponse)
def topup_account(
    payload: TopupRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = BillingService(db)
    org_id = 1
    return service.process_topup(org_id, payload.amount)

@router.post("/invoice", response_model=dict)
def create_invoice(
    payload: InvoiceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = BillingService(db)
    org_id = 1
    doc = service.generate_invoice(org_id, payload.amount)
    return {"id": doc.id, "url": doc.url, "number": doc.document_number}
