from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db, get_current_membership, get_current_org, get_current_user
from app.db.models import OrgProfile, Organization, User
from app.db.models_billing import BillingDocument, BillingTransaction
from app.services.billing import BillingService
from app.api.billing_schemas import BillingAccountResponse, TransactionResponse, TopupRequest, InvoiceRequest
from app.services.rbac import can_read_billing, can_write_billing

router = APIRouter(prefix="/billing", tags=["Billing"])

def _require_read(role: str) -> None:
    if not can_read_billing(role):
        raise HTTPException(status_code=403, detail="Недостаточно прав")


def _require_write(role: str) -> None:
    if not can_write_billing(role):
        raise HTTPException(status_code=403, detail="Недостаточно прав")

@router.get("/balance", response_model=BillingAccountResponse)
def get_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    membership=Depends(get_current_membership),
):
    _require_read(membership.role)
    service = BillingService(db)
    account = service.get_or_create_account(org.id)
    return {
        "id": account.id,
        "organization_id": account.organization_id,
        "balance": float(account.balance),
        "status": "active",
    }

@router.get("/transactions", response_model=List[TransactionResponse])
def list_transactions(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    membership=Depends(get_current_membership),
):
    _require_read(membership.role)
    transactions = db.query(BillingTransaction).filter(
        BillingTransaction.organization_id == org.id
    ).order_by(BillingTransaction.created_at.desc()).limit(limit).all()
    return [
        {
            "id": tx.id,
            "type": tx.type,
            "amount": float(tx.amount),
            "status": tx.status,
            "description": (tx.meta_json or {}).get("description"),
            "created_at": tx.created_at,
        }
        for tx in transactions
    ]

@router.post("/topup", response_model=BillingAccountResponse)
def topup_account(
    payload: TopupRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    membership=Depends(get_current_membership),
):
    _require_write(membership.role)
    service = BillingService(db)
    account = service.process_topup(org.id, payload.amount)
    return {
        "id": account.id,
        "organization_id": account.organization_id,
        "balance": float(account.balance),
        "status": "active",
    }


@router.post("/invoice")
def generate_invoice(
    payload: InvoiceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    membership=Depends(get_current_membership),
):
    _require_write(membership.role)
    from app.services.documents import generate_invoice_html
    import uuid

    invoice_number = f"INV-{uuid.uuid4().hex[:8].upper()}"
    profile = db.query(OrgProfile).filter(OrgProfile.organization_id == org.id).first()
    organization_name = profile.legal_name or org.name if profile else org.name
    currency = profile.currency if profile else "RUB"

    # Generate HTML content (could be converted to PDF with weasyprint)
    html_content = generate_invoice_html(
        organization_name=organization_name,
        invoice_number=invoice_number,
        amount=payload.amount,
        currency=currency,
    )
    
    # Save document record
    doc = BillingDocument(
        organization_id=org.id,
        type="invoice",
        number=invoice_number,
        status="draft",
        meta_json={"amount": payload.amount, "currency": currency, "html": html_content}
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
    current_user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    membership=Depends(get_current_membership),
):
    from fastapi.responses import HTMLResponse

    _require_read(membership.role)
    doc = (
        db.query(BillingDocument)
        .filter(
            BillingDocument.number == invoice_number,
            BillingDocument.organization_id == org.id,
        )
        .first()
    )
    if not doc or not doc.meta_json:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return HTMLResponse(content=doc.meta_json.get("html", "<p>No content</p>"))
