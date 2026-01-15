"""add org profiles

Revision ID: 0028_add_org_profiles
Revises: 0027_org_automation
Create Date: 2026-01-14 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0028_add_org_profiles"
down_revision = "0027_org_automation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "org_profiles",
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("legal_type", sa.String(length=20), nullable=True),
        sa.Column("legal_name", sa.String(length=255), nullable=True),
        sa.Column("inn", sa.String(length=20), nullable=True),
        sa.Column("kpp", sa.String(length=20), nullable=True),
        sa.Column("ogrn", sa.String(length=20), nullable=True),
        sa.Column("ogrnip", sa.String(length=20), nullable=True),
        sa.Column("legal_address", sa.String(length=500), nullable=True),
        sa.Column("email_for_docs", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default=sa.text("'Europe/Moscow'")),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default=sa.text("'RUB'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("org_profiles")
