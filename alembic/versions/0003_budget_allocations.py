"""budget allocations

Revision ID: 0003_budget_allocations
Revises: 0002_conversion_events
Create Date: 2024-01-03 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_budget_allocations"

down_revision = "0002_conversion_events"

branch_labels = None

depends_on = None


def upgrade() -> None:
    op.create_table(
        "budget_allocations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("experiment_id", sa.Integer(), sa.ForeignKey("experiments.id"), nullable=False),
        sa.Column("platform", sa.Enum("yandex", "ozon", "vk", name="platform"), nullable=False),
        sa.Column(
            "creative_variant_id",
            sa.Integer(),
            sa.ForeignKey("creative_variants.id"),
            nullable=True,
        ),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("budget_allocations")
