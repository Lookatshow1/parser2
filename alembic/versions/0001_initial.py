"""initial

Revision ID: 0001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"

down_revision = None

branch_labels = None

depends_on = None


platform_enum = sa.Enum("yandex", "ozon", "vk", name="platform")
connection_status_enum = sa.Enum("active", "inactive", "error", name="connectionstatus")
experiment_status_enum = sa.Enum("planned", "running", "stopped", "completed", name="experimentstatus")


def upgrade() -> None:
    platform_enum.create(op.get_bind(), checkfirst=True)
    connection_status_enum.create(op.get_bind(), checkfirst=True)
    experiment_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "advertisers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "campaign_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("advertiser_id", sa.Integer(), sa.ForeignKey("advertisers.id"), nullable=True),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("business_description", sa.Text(), nullable=True),
        sa.Column("kpi", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "connections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("advertiser_id", sa.Integer(), sa.ForeignKey("advertisers.id"), nullable=True),
        sa.Column("platform", platform_enum, nullable=False),
        sa.Column("credentials_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", connection_status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "experiments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("campaign_plans.id"), nullable=False),
        sa.Column("status", experiment_status_enum, nullable=False),
        sa.Column("start_at", sa.DateTime(), nullable=True),
        sa.Column("end_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "creative_variants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("experiment_id", sa.Integer(), sa.ForeignKey("experiments.id"), nullable=False),
        sa.Column("platform", platform_enum, nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(length=2048), nullable=True),
        sa.Column("meta_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "metric_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("platform", platform_enum, nullable=False),
        sa.Column("campaign_external_id", sa.String(length=255), nullable=False),
        sa.Column("clicks", sa.Integer(), nullable=False),
        sa.Column("impressions", sa.Integer(), nullable=False),
        sa.Column("spend", sa.Integer(), nullable=False),
        sa.Column("leads", sa.Integer(), nullable=False),
        sa.Column("purchases", sa.Integer(), nullable=False),
        sa.Column("revenue", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )



def downgrade() -> None:
    op.drop_table("metric_snapshots")
    op.drop_table("creative_variants")
    op.drop_table("experiments")
    op.drop_table("connections")
    op.drop_table("campaign_plans")
    op.drop_table("advertisers")

    experiment_status_enum.drop(op.get_bind(), checkfirst=True)
    connection_status_enum.drop(op.get_bind(), checkfirst=True)
    platform_enum.drop(op.get_bind(), checkfirst=True)
