"""add updated_at to metric_snapshots

Revision ID: 0005_metric_snapshots_updated_at
Revises: 0004_job_status_values
Create Date: 2026-01-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0005_metric_snapshots_updated_at"
down_revision = "0004_job_status_values"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "metric_snapshots",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("metric_snapshots", "updated_at")
