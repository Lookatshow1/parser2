"""add erid to draft_ads

Revision ID: 0031_add_erid
Revises: b8b764f7515c
Create Date: 2026-01-31
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0031_add_erid'
down_revision: Union[str, None] = 'b8b764f7515c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add ERID field to draft_ads table for Russian advertising law compliance
    # ERID = Единый Реестр Интернет-Рекламы (ЕРИ Р)
    op.add_column('draft_ads', sa.Column('erid', sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column('draft_ads', 'erid')
