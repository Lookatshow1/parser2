"""budget allocations

Revision ID: 0003_budget_allocations
Revises: 0002_conversion_events
Create Date: 2025-12-30 21:34:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0003_budget_allocations"
down_revision: Union[str, None] = "0002_conversion_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    platform_enum = postgresql.ENUM(
        "yandex",
        "ozon",
        "vk",
        name="platform_enum",
        create_type=False,
    )

    op.create_table(
        "budget_allocations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "plan_id",
            sa.Integer(),
            sa.ForeignKey("campaign_plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "experiment_id",
            sa.Integer(),
            sa.ForeignKey("experiments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "creative_variant_id",
            sa.Integer(),
            sa.ForeignKey("creative_variants.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("platform", platform_enum, nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("allocated_budget", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("spent_budget", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "plan_id",
            "platform",
            "date",
            "creative_variant_id",
            name="uq_budget_allocations_plan_platform_date_creative",
        ),
    )


def downgrade() -> None:
    op.drop_table("budget_allocations")
