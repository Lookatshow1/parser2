"""org invite status and membership created_at

Revision ID: 0011_org_invite_status_and_membership_created_at
Revises: 0010_refresh_tokens
Create Date: 2026-01-07 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0011_org_invite_status_and_membership_created_at"
down_revision = "0010_refresh_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "organization_members",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.add_column(
        "org_invites",
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
    )
    op.create_index("idx_org_invites_status", "org_invites", ["status"], unique=False)



def downgrade() -> None:
    op.drop_index("idx_org_invites_status", table_name="org_invites")
    op.drop_column("org_invites", "status")
    op.drop_column("organization_members", "created_at")
