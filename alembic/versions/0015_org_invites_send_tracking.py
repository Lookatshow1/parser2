"""org invites send tracking

Revision ID: 0015_org_invites_send_tracking
Revises: 0014_org_audit_events
Create Date: 2026-01-15 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0015_org_invites_send_tracking"
down_revision = "0014_org_audit_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("org_invites", sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "org_invites",
        sa.Column("send_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column("org_invites", sa.Column("last_error", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("org_invites", "last_error")
    op.drop_column("org_invites", "send_count")
    op.drop_column("org_invites", "sent_at")
