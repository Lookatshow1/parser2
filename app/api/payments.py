"""
YooKassa Payment API Endpoints.

Handles payment creation and webhooks.
"""
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.api.deps import get_current_org_id
from app.services.yookassa_service import YooKassaService

router = APIRouter(prefix="/payments", tags=["Payments"])


class CreatePaymentRequest(BaseModel):
    amount: float
    description: Optional[str] = "Пополнение баланса"
    return_url: Optional[str] = None


class CreatePaymentResponse(BaseModel):
    payment_id: Optional[str] = None
    status: Optional[str] = None
    confirmation_url: Optional[str] = None
    amount: Optional[float] = None
    error: Optional[str] = None
    demo_mode: Optional[bool] = False


class WebhookResponse(BaseModel):
    status: str
    org_id: Optional[int] = None
    amount: Optional[float] = None
    event: Optional[str] = None


@router.post("/create", response_model=CreatePaymentResponse)
async def create_payment(
    payload: CreatePaymentRequest,
    db: Session = Depends(get_db),
    org_id: int = Depends(get_current_org_id)
):
    """
    Create a new payment for balance top-up.
    
    Returns confirmation URL for redirect to YooKassa payment page.
    """
    service = YooKassaService(db)
    
    if not service.is_configured:
        # Demo mode - simulate payment
        return CreatePaymentResponse(
            payment_id="demo_" + str(org_id),
            status="demo",
            confirmation_url=None,
            amount=payload.amount,
            demo_mode=True,
            error="YooKassa не настроен. Добавьте YOOKASSA_SHOP_ID и YOOKASSA_SECRET_KEY в .env"
        )
    
    result = await service.create_payment(
        org_id=org_id,
        amount=payload.amount,
        description=payload.description,
        return_url=payload.return_url
    )
    
    return CreatePaymentResponse(**result)


@router.get("/check/{payment_id}")
async def check_payment(
    payment_id: str,
    db: Session = Depends(get_db)
):
    """Check payment status by ID."""
    service = YooKassaService(db)
    return await service.check_payment(payment_id)


@router.post("/webhook", response_model=WebhookResponse)
async def payment_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Webhook endpoint for YooKassa notifications.
    
    YooKassa will call this when payment status changes.
    Must be accessible from internet.
    """
    try:
        payload = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    # Optional: verify signature
    signature = request.headers.get("X-YooKassa-Signature")
    
    service = YooKassaService(db)
    result = service.process_webhook(payload, signature)
    
    return WebhookResponse(**result)


@router.post("/demo-topup")
async def demo_topup(
    payload: CreatePaymentRequest,
    db: Session = Depends(get_db),
    org_id: int = Depends(get_current_org_id)
):
    """
    Demo endpoint for testing balance top-up without real payment.
    
    Only works when YooKassa is not configured.
    """
    service = YooKassaService(db)
    
    if service.is_configured:
        raise HTTPException(400, "Use real payment endpoint when YooKassa is configured")
    
    # Simulate successful payment
    from app.db.models_billing import BillingTransaction
    
    tx = BillingTransaction(
        organization_id=org_id,
        type="topup",
        amount=payload.amount,
        status="completed",
        external_id=f"demo_{org_id}_{payload.amount}"
    )
    db.add(tx)
    db.commit()
    
    return {
        "status": "credited",
        "amount": payload.amount,
        "demo_mode": True,
        "message": "Демо-пополнение выполнено"
    }
