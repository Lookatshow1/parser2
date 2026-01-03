"""conversion events

Revision ID: 0002_conversion_events
Revises: 0001_initial
Create Date: 2025-12-30 21:24:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0002_conversion_events"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conversion_event_type = postgresql.ENUM(
        "lead",
        "purchase",
        name="conversioneventtype",
        create_type=False,
    )
    conversion_event_type.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "campaign_plans",
        sa.Column("internal_code", sa.String(length=64), nullable=True),
    )

    op.create_table(
        "conversion_events",
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
        sa.Column("type", conversion_event_type, nullable=False),
        sa.Column("value", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("meta_json", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("conversion_events")
    op.drop_column("campaign_plans", "internal_code")
    op.execute("DROP TYPE IF EXISTS conversioneventtype")
