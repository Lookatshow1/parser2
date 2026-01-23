from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime


class RagIngestRequest(BaseModel):
    source_type: str = Field(..., description="Тип источника: website, competitor, manual, campaign")
    source_id: int | None = None
    title: str | None = None
    url: str | None = None
    text: str | None = None
    meta: dict | None = None


class RagDocumentOut(BaseModel):
    id: int
    source_type: str
    source_id: int | None = None
    title: str | None = None
    url: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RagSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    source_types: list[str] | None = None


class RagSearchItem(BaseModel):
    chunk_id: int
    document_id: int
    score: float
    text: str
    source_type: str
    title: str | None = None
    url: str | None = None


class RagSearchResponse(BaseModel):
    items: list[RagSearchItem]
