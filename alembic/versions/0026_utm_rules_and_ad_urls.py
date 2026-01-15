"""utm rules and ad urls

Revision ID: 0026_utm_rules_and_ad_urls
Revises: 0025_add_campaign_entities
Create Date: 2026-01-14 13:30:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0026_utm_rules_and_ad_urls"
down_revision = "0025_add_campaign_entities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ad_ads", sa.Column("target_url", sa.Text(), nullable=True))
    op.add_column("ad_ads", sa.Column("final_url", sa.Text(), nullable=True))
    op.add_column("ad_ads", sa.Column("utm_applied_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("ad_ads", sa.Column("utm_hash", sa.String(length=64), nullable=True))
    op.add_column("ad_ads", sa.Column("url_status", sa.String(length=50), nullable=True))

    op.create_table(
        "org_utm_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("match_platform", postgresql.ENUM("yandex", "ozon", "vk", "stub", name="platform_enum", create_type=False), nullable=True),
        sa.Column("match_connection_id", sa.Integer(), nullable=True),
        sa.Column("match_campaign_contains", sa.String(length=255), nullable=True),
        sa.Column("match_ad_group_contains", sa.String(length=255), nullable=True),
        sa.Column("match_ad_contains", sa.String(length=255), nullable=True),
        sa.Column("template_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_org_utm_rules_org_enabled", "org_utm_rules", ["organization_id", "is_enabled"])


def downgrade() -> None:
    op.drop_index("idx_org_utm_rules_org_enabled", table_name="org_utm_rules")
    op.drop_table("org_utm_rules")

    op.drop_column("ad_ads", "url_status")
    op.drop_column("ad_ads", "utm_hash")
    op.drop_column("ad_ads", "utm_applied_at")
    op.drop_column("ad_ads", "final_url")
    op.drop_column("ad_ads", "target_url")
