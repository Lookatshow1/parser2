from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_org
from app.db.session import get_db
from app.db.models import Organization
from app.api.rag_schemas import (
    RagIngestRequest,
    RagDocumentOut,
    RagSearchRequest,
    RagSearchResponse,
    RagSearchItem,
)
from app.services.rag_service import RagService
from app.services.website_parser import WebsiteParserService
from app.db.models_rag import RagDocument


router = APIRouter(prefix="/rag", tags=["rag"])


@router.get("", response_model=list[RagDocumentOut])
def list_documents(
    source_type: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    q = db.query(RagDocument).filter(RagDocument.organization_id == org.id)
    if source_type:
        q = q.filter(RagDocument.source_type == source_type)
    return q.order_by(RagDocument.created_at.desc()).limit(limit).all()


@router.post("/ingest", response_model=RagDocumentOut)
async def ingest_document(
    payload: RagIngestRequest,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    text = (payload.text or "").strip()
    title = payload.title
    source_id = payload.source_id
    meta = payload.meta or {}

    if not text and payload.url:
        parser = WebsiteParserService(db)
        context = await parser.parse_and_save(payload.url, org.id)
        text = (context.clean_text or "").strip()
        if not title:
            title = context.meta_title
        meta = {
            **meta,
            "meta_title": context.meta_title,
            "meta_description": context.meta_description,
            "context_id": context.id,
        }
        if payload.source_type == "website" and source_id is None:
            source_id = context.id

    if not text:
        raise HTTPException(status_code=400, detail="Нет текста для индексации")

    service = RagService(db)
    doc = await service.ingest_text(
        organization_id=org.id,
        source_type=payload.source_type,
        source_id=source_id,
        title=title,
        url=payload.url,
        text=text,
        meta=meta,
    )
    return doc


@router.post("/search", response_model=RagSearchResponse)
async def search_rag(
    payload: RagSearchRequest,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    service = RagService(db)
    results = await service.search(
        organization_id=org.id,
        query=payload.query,
        top_k=payload.top_k,
        source_types=payload.source_types,
    )
    items = [RagSearchItem(**item) for item in results]
    return RagSearchResponse(items=items)
