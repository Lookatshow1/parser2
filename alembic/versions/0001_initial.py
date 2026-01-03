"""initial

Revision ID: 0001_initial
Revises:
Create Date: 2025-12-30 21:14:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    platform_enum = postgresql.ENUM(
        "yandex", "ozon", "vk", name="platform_enum", create_type=False
    )
    connection_status_enum = postgresql.ENUM(
        "active",
        "inactive",
        "error",
        name="connection_status_enum",
        create_type=False,
    )
    experiment_status_enum = postgresql.ENUM(
        "draft",
        "running",
        "stopped",
        "completed",
        name="experiment_status_enum",
        create_type=False,
    )
    creative_status_enum = postgresql.ENUM(
        "draft",
        "approved",
        "rejected",
        "active",
        "paused",
        name="creative_status_enum",
        create_type=False,
    )

    platform_enum.create(op.get_bind(), checkfirst=True)
    connection_status_enum.create(op.get_bind(), checkfirst=True)
    experiment_status_enum.create(op.get_bind(), checkfirst=True)
    creative_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "advertisers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "campaign_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "advertiser_id",
            sa.Integer(),
            sa.ForeignKey("advertisers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("platform", platform_enum, nullable=False),
        sa.Column("budget", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="RUB"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "connections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "advertiser_id",
            sa.Integer(),
            sa.ForeignKey("advertisers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("platform", platform_enum, nullable=False),
        sa.Column("status", connection_status_enum, nullable=False, server_default="active"),
        sa.Column("credentials_json", postgresql.JSONB(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "experiments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "plan_id",
            sa.Integer(),
            sa.ForeignKey("campaign_plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", experiment_status_enum, nullable=False, server_default="draft"),
        sa.Column("settings_json", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "creative_variants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "experiment_id",
            sa.Integer(),
            sa.ForeignKey("experiments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", creative_status_enum, nullable=False, server_default="draft"),
        sa.Column("payload_json", postgresql.JSONB(), nullable=True),
        sa.Column("external_creative_id", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "metric_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "experiment_id",
            sa.Integer(),
            sa.ForeignKey("experiments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "creative_variant_id",
            sa.Integer(),
            sa.ForeignKey("creative_variants.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("metrics_json", postgresql.JSONB(), nullable=False),
        sa.Column(
            "collected_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("metric_snapshots")
    op.drop_table("creative_variants")
    op.drop_table("experiments")
    op.drop_table("connections")
    op.drop_table("campaign_plans")
    op.drop_table("advertisers")

    op.execute("DROP TYPE IF EXISTS creative_status_enum")
    op.execute("DROP TYPE IF EXISTS experiment_status_enum")
    op.execute("DROP TYPE IF EXISTS connection_status_enum")
    op.execute("DROP TYPE IF EXISTS platform_enum")
