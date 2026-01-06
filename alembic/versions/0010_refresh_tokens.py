"""refresh tokens

Revision ID: 0010_refresh_tokens
Revises: 0009_org_invites
Create Date: 2026-01-07 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0010_refresh_tokens"
down_revision = "0009_org_invites"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("jti", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("uq_refresh_tokens_hash", "refresh_tokens", ["token_hash"], unique=True)
    op.create_index("uq_refresh_tokens_jti", "refresh_tokens", ["jti"], unique=True)
    op.create_index("idx_refresh_tokens_user_id", "refresh_tokens", ["user_id"], unique=False)
    op.create_index("idx_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_refresh_tokens_expires_at", table_name="refresh_tokens")
    op.drop_index("idx_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_index("uq_refresh_tokens_jti", table_name="refresh_tokens")
    op.drop_index("uq_refresh_tokens_hash", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
