"""connection auto sync fields

Revision ID: 0012_connection_auto_sync_fields
Revises: 0011_org_invite_status_and_membership_created_at
Create Date: 2026-01-07 13:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0012_connection_auto_sync_fields"
down_revision = "0011_org_invite_status_and_membership_created_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "connections",
        sa.Column("auto_sync_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "connections",
        sa.Column("auto_sync_every_minutes", sa.Integer(), nullable=False, server_default="1440"),
    )
    op.add_column(
        "connections",
        sa.Column("auto_sync_window_days", sa.Integer(), nullable=False, server_default="3"),
    )
    op.add_column(
        "connections",
        sa.Column("last_auto_sync_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("connections", "last_auto_sync_at")
    op.drop_column("connections", "auto_sync_window_days")
    op.drop_column("connections", "auto_sync_every_minutes")
    op.drop_column("connections", "auto_sync_enabled")
