"""org invites revoked fields

Revision ID: 0013_org_invites_revoked_fields
Revises: 0012_connection_auto_sync_fields
Create Date: 2026-01-08 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0013_org_invites_revoked_fields"
down_revision = "0012_connection_auto_sync_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("org_invites", sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("org_invites", sa.Column("revoked_by_user_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_org_invites_revoked_by_user",
        "org_invites",
        "users",
        ["revoked_by_user_id"],
        ["id"],
    )
    op.create_index("idx_org_invites_org_id", "org_invites", ["organization_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_org_invites_org_id", table_name="org_invites")
    op.drop_constraint("fk_org_invites_revoked_by_user", "org_invites", type_="foreignkey")
    op.drop_column("org_invites", "revoked_by_user_id")
    op.drop_column("org_invites", "revoked_at")
