"""creative compliance token

Revision ID: 0004_creative_compliance_token
Revises: 0003_budget_allocations
Create Date: 2024-01-04 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_creative_compliance_token"

down_revision = "0003_budget_allocations"

branch_labels = None

depends_on = None


def upgrade() -> None:
    op.add_column("creative_variants", sa.Column("compliance_token", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("creative_variants", "compliance_token")
