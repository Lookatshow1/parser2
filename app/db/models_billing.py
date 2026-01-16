import enum
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import ForeignKey, Integer, String, Text, DateTime, func, Numeric, Date
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class TransactionType(str, enum.Enum):
    topup = "topup"
    spend = "spend"
    refund = "refund"
    adjustment = "adjustment"

class TransactionStatus(str, enum.Enum):
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"

class DocumentType(str, enum.Enum):
    invoice = "invoice"
    act = "act"
    contract = "contract"
    offer = "offer"

class DocumentStatus(str, enum.Enum):
    draft = "draft"
    sent = "sent"
    signed = "signed"

class BillingAccount(Base):
    __tablename__ = "billing_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    currency: Mapped[str] = mapped_column(String(3), default="RUB", nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    reserved_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    organization = relationship("Organization") # Backref might need to be added to Organization if needed


class BillingTransaction(Base):
    __tablename__ = "billing_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    type: Mapped[TransactionType] = mapped_column(String, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[TransactionStatus] = mapped_column(String, default=TransactionStatus.pending, nullable=False)
    
    provider: Mapped[str | None] = mapped_column(String, nullable=True) # e.g. stripe, yookassa, mock
    external_id: Mapped[str | None] = mapped_column(String, nullable=True)
    meta_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    organization = relationship("Organization")


class BillingDocument(Base):
    __tablename__ = "billing_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    type: Mapped[DocumentType] = mapped_column(String, nullable=False)
    number: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(String, default=DocumentStatus.draft, nullable=False)
    
    period_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    file_path: Mapped[str | None] = mapped_column(String, nullable=True)
    meta_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    organization = relationship("Organization")
