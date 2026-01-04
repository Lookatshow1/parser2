"""add experiment_campaigns

Revision ID: 0007_experiment_campaigns
Revises: 0006_add_plan_connection
Create Date: 2026-01-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0007_experiment_campaigns"
down_revision = "0006_add_plan_connection"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # reuse existing enum type
    platform_enum = postgresql.ENUM("yandex", "ozon", "vk", name="platform_enum", create_type=False)
    platform_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "experiment_campaigns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("experiment_id", sa.Integer(), sa.ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform", sa.Enum("yandex", "ozon", "vk", name="platform_enum"), nullable=False),
        sa.Column("campaign_external_id", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("experiment_id", "platform", "campaign_external_id", name="uq_experiment_campaign"),
    )


def downgrade() -> None:
    op.drop_table("experiment_campaigns")
