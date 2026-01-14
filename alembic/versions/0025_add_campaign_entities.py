"""add campaigns builder entities

Revision ID: 0025_add_campaign_entities
Revises: 0024_add_plan_support_to_builder
Create Date: 2026-01-13 21:10:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0025_add_campaign_entities"
down_revision = "0024_add_plan_support_to_builder"
branch_labels = None
depends_on = None


def upgrade() -> None:
    platform_enum = postgresql.ENUM("yandex", "ozon", "vk", "stub", name="platform_enum", create_type=False)
    status_enum = postgresql.ENUM("draft", "active", "paused", "archived", name="campaign_status_enum", create_type=True)
    op.create_table(
        "campaigns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform", platform_enum, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("objective", sa.String(length=255), nullable=True),
        sa.Column("status", status_enum, nullable=False, server_default="draft"),
        sa.Column("budget_total", sa.Numeric(14, 2), nullable=True),
        sa.Column("budget_daily", sa.Numeric(14, 2), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_campaigns_org_platform_status", "campaigns", ["organization_id", "platform", "status"])

    op.create_table(
        "ad_groups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", status_enum, nullable=False, server_default="draft"),
        sa.Column("bid_strategy", sa.String(length=255), nullable=True),
        sa.Column("budget_daily", sa.Numeric(14, 2), nullable=True),
        sa.Column("targeting_json", sa.JSON(), nullable=False, server_default='{}'),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_ad_groups_campaign_status", "ad_groups", ["campaign_id", "status"])

    op.create_table(
        "ads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ad_group_id", sa.Integer(), sa.ForeignKey("ad_groups.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", status_enum, nullable=False, server_default="draft"),
        sa.Column("creative_json", sa.JSON(), nullable=False, server_default='{}'),
        sa.Column("landing_url", sa.String(length=2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_ads_ad_group_status", "ads", ["ad_group_id", "status"])

    op.create_table(
        "campaign_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False, server_default='{}'),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_campaign_events_org_created", "campaign_events", ["organization_id", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_campaign_events_org_created", table_name="campaign_events")
    op.drop_table("campaign_events")

    op.drop_index("idx_ads_ad_group_status", table_name="ads")
    op.drop_table("ads")

    op.drop_index("idx_ad_groups_campaign_status", table_name="ad_groups")
    op.drop_table("ad_groups")

    op.drop_index("idx_campaigns_org_platform_status", table_name="campaigns")
    op.drop_table("campaigns")

    op.execute("DROP TYPE IF EXISTS campaign_status_enum")
