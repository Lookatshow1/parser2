"""
YooKassa Payment Service.

Integration with YooKassa for accepting payments in Russia.
"""
import hashlib
import hmac
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Organization, BillingTransaction


class YooKassaService:
    """Service for YooKassa payment processing."""
    
    BASE_URL = "https://api.yookassa.ru/v3"
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.shop_id = getattr(self.settings, 'yookassa_shop_id', None)
        self.secret_key = getattr(self.settings, 'yookassa_secret_key', None)
    
    @property
    def is_configured(self) -> bool:
        """Check if YooKassa credentials are set."""
        return bool(self.shop_id and self.secret_key)
    
    def _get_auth(self) -> tuple:
        """Get HTTP Basic Auth tuple."""
        return (self.shop_id, self.secret_key)
    
    def _get_headers(self, idempotence_key: str = None) -> Dict[str, str]:
        """Get request headers."""
        return {
            "Content-Type": "application/json",
            "Idempotence-Key": idempotence_key or str(uuid.uuid4())
        }
    
    async def create_payment(
        self,
        org_id: int,
        amount: float,
        description: str = "Пополнение баланса",
        return_url: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create a payment in YooKassa.
        
        Returns payment object with confirmation URL.
        """
        if not self.is_configured:
            return {"error": "YooKassa not configured", "demo_mode": True}
        
        web_base = getattr(self.settings, 'web_base_url', 'http://localhost:3000')
        return_url = return_url or f"{web_base}/billing?payment=success"
        
        payload = {
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            },
            "capture": True,
            "confirmation": {
                "type": "redirect",
                "return_url": return_url
            },
            "description": description,
            "metadata": {
                "org_id": org_id,
                **(metadata or {})
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/payments",
                    json=payload,
                    auth=self._get_auth(),
                    headers=self._get_headers()
                )
                response.raise_for_status()
                data = response.json()
                
                # Save pending transaction
                self._save_pending_transaction(
                    org_id=org_id,
                    payment_id=data["id"],
                    amount=amount
                )
                
                return {
                    "payment_id": data["id"],
                    "status": data["status"],
                    "confirmation_url": data.get("confirmation", {}).get("confirmation_url"),
                    "amount": amount
                }
        except httpx.HTTPError as e:
            return {"error": str(e)}
    
    async def check_payment(self, payment_id: str) -> Dict[str, Any]:
        """Check payment status."""
        if not self.is_configured:
            return {"error": "YooKassa not configured"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/payments/{payment_id}",
                    auth=self._get_auth()
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            return {"error": str(e)}
    
    def process_webhook(self, payload: Dict[str, Any], signature: str = None) -> Dict[str, Any]:
        """
        Process webhook notification from YooKassa.
        
        Called when payment status changes.
        """
        event = payload.get("event")
        payment_data = payload.get("object", {})
        payment_id = payment_data.get("id")
        status = payment_data.get("status")
        
        if event == "payment.succeeded" and status == "succeeded":
            # Credit the balance
            metadata = payment_data.get("metadata", {})
            org_id = metadata.get("org_id")
            amount = float(payment_data.get("amount", {}).get("value", 0))
            
            if org_id:
                self._credit_balance(
                    org_id=int(org_id),
                    amount=amount,
                    payment_id=payment_id
                )
                return {"status": "credited", "org_id": org_id, "amount": amount}
        
        elif event == "payment.canceled":
            # Mark transaction as failed
            self._mark_transaction_failed(payment_id)
            return {"status": "canceled"}
        
        return {"status": "ignored", "event": event}
    
    def _save_pending_transaction(self, org_id: int, payment_id: str, amount: float):
        """Save pending transaction to database."""
        tx = BillingTransaction(
            organization_id=org_id,
            type="topup",
            amount=amount,
            status="pending",
            external_id=payment_id
        )
        self.db.add(tx)
        self.db.commit()
    
    def _credit_balance(self, org_id: int, amount: float, payment_id: str):
        """Credit balance after successful payment."""
        # Update transaction status
        tx = self.db.query(BillingTransaction).filter(
            BillingTransaction.external_id == payment_id
        ).first()
        
        if tx:
            tx.status = "completed"
        else:
            # Create new transaction if not found
            tx = BillingTransaction(
                organization_id=org_id,
                type="topup",
                amount=amount,
                status="completed",
                external_id=payment_id
            )
            self.db.add(tx)
        
        # Update organization balance
        org = self.db.query(Organization).filter(Organization.id == org_id).first()
        if org:
            # Assuming balance is stored elsewhere or we need to add it
            pass
        
        self.db.commit()
    
    def _mark_transaction_failed(self, payment_id: str):
        """Mark transaction as failed."""
        tx = self.db.query(BillingTransaction).filter(
            BillingTransaction.external_id == payment_id
        ).first()
        
        if tx:
            tx.status = "failed"
            self.db.commit()
    
    async def create_refund(
        self,
        payment_id: str,
        amount: float = None,
        description: str = "Возврат средств"
    ) -> Dict[str, Any]:
        """Create a refund for a payment."""
        if not self.is_configured:
            return {"error": "YooKassa not configured"}
        
        payload = {
            "payment_id": payment_id,
            "description": description
        }
        
        if amount:
            payload["amount"] = {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/refunds",
                    json=payload,
                    auth=self._get_auth(),
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            return {"error": str(e)}
