from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db, get_current_user
from app.db.models import User
from app.db.models_billing import BillingTransaction
from app.services.billing import BillingService
from app.api.billing_schemas import BillingAccountResponse, TransactionResponse, TopupRequest, InvoiceRequest

router = APIRouter(prefix="/billing", tags=["Billing"])

@router.get("/balance", response_model=BillingAccountResponse)
def get_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = BillingService(db)
    org_id = 1  # TODO: Get from context
    return service.get_or_create_account(org_id)

@router.get("/transactions", response_model=List[TransactionResponse])
def list_transactions(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    org_id = 1  # TODO: Get from context
    transactions = db.query(BillingTransaction).filter(
        BillingTransaction.organization_id == org_id
    ).order_by(BillingTransaction.created_at.desc()).limit(limit).all()
    return transactions

@router.post("/topup", response_model=BillingAccountResponse)
def topup_account(
    payload: TopupRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = BillingService(db)
    org_id = 1
    return service.process_topup(org_id, payload.amount)


@router.post("/invoice")
def generate_invoice(
    payload: InvoiceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.services.documents import generate_invoice_html
    from app.db.models_billing import BillingDocument
    import uuid
    
    org_id = 1
    invoice_number = f"INV-{uuid.uuid4().hex[:8].upper()}"
    
    # Generate HTML content (could be converted to PDF with weasyprint)
    html_content = generate_invoice_html(
        organization_name="Demo Organization",
        invoice_number=invoice_number,
        amount=payload.amount,
        currency="RUB"
    )
    
    # Save document record
    doc = BillingDocument(
        organization_id=org_id,
        type="invoice",
        number=invoice_number,
        status="draft",
        meta_json={"amount": payload.amount, "html": html_content}
    )
    db.add(doc)
    db.commit()
    
    return {
        "id": doc.id,
        "number": invoice_number,
        "amount": payload.amount,
        "html": html_content
    }


@router.get("/invoice/{invoice_number}/html")
def get_invoice_html(
    invoice_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from fastapi.responses import HTMLResponse
    from app.db.models_billing import BillingDocument
    
    doc = db.query(BillingDocument).filter(BillingDocument.number == invoice_number).first()
    if not doc or not doc.meta_json:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return HTMLResponse(content=doc.meta_json.get("html", "<p>No content</p>"))
