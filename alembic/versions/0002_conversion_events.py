"""conversion events

Revision ID: 0002_conversion_events
Revises: 0001_initial
Create Date: 2024-01-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_conversion_events"

down_revision = "0001_initial"

branch_labels = None

depends_on = None


event_type_enum = sa.Enum("lead", "purchase", name="conversioneventtype")


def upgrade() -> None:
    event_type_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "campaign_plans",
        sa.Column("internal_code", sa.String(length=255), nullable=True, unique=True),
    )

    op.create_table(
        "conversion_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.String(length=36), nullable=False, unique=True),
        sa.Column("event_type", event_type_enum, nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("landing_url", sa.String(length=2048), nullable=False),
        sa.Column("utm_source", sa.String(length=255), nullable=True),
        sa.Column("utm_medium", sa.String(length=255), nullable=True),
        sa.Column("utm_campaign", sa.String(length=255), nullable=True),
        sa.Column("utm_content", sa.String(length=255), nullable=True),
        sa.Column("utm_term", sa.String(length=255), nullable=True),
        sa.Column("contact_phone", sa.String(length=64), nullable=True),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("value", sa.Integer(), nullable=True),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("campaign_plans.id"), nullable=True),
        sa.Column("experiment_id", sa.Integer(), sa.ForeignKey("experiments.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("conversion_events")
    op.drop_column("campaign_plans", "internal_code")
    event_type_enum.drop(op.get_bind(), checkfirst=True)
