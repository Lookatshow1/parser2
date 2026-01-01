from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CreativeVariant


class ComplianceRegistry:
    def register(self, session: Session, creative_variant_id: int, token: str) -> CreativeVariant:
        creative = session.scalar(
            select(CreativeVariant).where(CreativeVariant.id == creative_variant_id)
        )
        if creative is None:
            raise ValueError("CreativeVariant not found")
        creative.compliance_token = token
        session.commit()
        session.refresh(creative)
        return creative
