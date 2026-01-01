from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.schemas import EventResponse, LeadEventRequest, PurchaseEventRequest
from app.db.models import ConversionEventType
from app.db.session import get_db
from app.services.event_service import EventService

router = APIRouter(prefix="/events")


@router.post("/lead", response_model=EventResponse)
def create_lead_event(
    payload: LeadEventRequest,
    session: Session = Depends(get_db),
):
    service = EventService()
    _, idempotent = service.handle_event(session, ConversionEventType.lead, payload)
    return EventResponse(ok=True, idempotent=idempotent)


@router.post("/purchase", response_model=EventResponse)
def create_purchase_event(
    payload: PurchaseEventRequest,
    session: Session = Depends(get_db),
):
    service = EventService()
    _, idempotent = service.handle_event(session, ConversionEventType.purchase, payload)
    return EventResponse(ok=True, idempotent=idempotent)
