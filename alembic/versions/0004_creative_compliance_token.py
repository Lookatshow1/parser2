"""creative compliance token

Revision ID: 0004_creative_compliance_token
Revises: 0003_budget_allocations
Create Date: 2025-12-30 21:44:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0004_creative_compliance_token"
down_revision: Union[str, None] = "0003_budget_allocations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "creative_variants",
        sa.Column("compliance_token", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_creative_variants_compliance_token",
        "creative_variants",
        ["compliance_token"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_creative_variants_compliance_token", table_name="creative_variants")
    op.drop_column("creative_variants", "compliance_token")
