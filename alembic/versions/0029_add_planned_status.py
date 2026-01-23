"""add planned status to experiment_status_enum

Revision ID: 0029_add_planned_status
Revises: 68d5943d632e
Create Date: 2026-01-23 22:25:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0029_add_planned_status'
down_revision = '68d5943d632e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add 'planned' to experiment_status_enum
    # Postgres doesn't allow adding values to enum inside a transaction easily in older versions,
    # but for modern Postgres we can use ALTER TYPE.
    # alembic-autogenerate usually handles this with op.execute("ALTER TYPE ... ADD VALUE ...")
    op.execute("ALTER TYPE experiment_status_enum ADD VALUE 'planned' AFTER 'draft'")


def downgrade() -> None:
    # Removing a value from an enum is not supported by Postgres without recreating the type.
    # We'll leave it as is or provide a no-op.
    pass
