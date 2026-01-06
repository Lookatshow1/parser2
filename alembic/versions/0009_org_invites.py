"""org invites

Revision ID: 0009_org_invites
Revises: 0008_auth_and_memberships
Create Date: 2026-01-06 20:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_org_invites"
down_revision = "0008_auth_and_memberships"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "org_invites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("invited_email", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["accepted_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
    )

    op.create_index("idx_org_invites_email", "org_invites", ["invited_email"], unique=False)
    op.create_index("uq_org_invites_token_hash", "org_invites", ["token_hash"], unique=True)
    op.create_index(
        "uq_org_invites_active",
        "org_invites",
        ["organization_id", "invited_email"],
        unique=True,
        postgresql_where=sa.text("accepted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_org_invites_active", table_name="org_invites")
    op.drop_index("uq_org_invites_token_hash", table_name="org_invites")
    op.drop_index("idx_org_invites_email", table_name="org_invites")
    op.drop_table("org_invites")
