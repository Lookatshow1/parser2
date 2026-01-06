"""metric snapshot connection indexes

Revision ID: 0007_metric_snapshot_connection_indexes
Revises: 0006_add_erir_dev_fields
Create Date: 2026-01-06 15:05:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0007_metric_snapshot_connection_indexes"
down_revision = "0006_add_erir_dev_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "uq_metric_connection_ad_group",
        "metric_snapshots",
        [
            "organization_id",
            "connection_id",
            "platform",
            "date",
            "campaign_external_id",
            "ad_group_external_id",
        ],
        unique=True,
        postgresql_where=sa.text("level = 'ad_group' AND connection_id IS NOT NULL"),
    )
    op.create_index(
        "uq_metric_connection_ad",
        "metric_snapshots",
        [
            "organization_id",
            "connection_id",
            "platform",
            "date",
            "campaign_external_id",
            "ad_group_external_id",
            "ad_external_id",
        ],
        unique=True,
        postgresql_where=sa.text("level = 'ad' AND connection_id IS NOT NULL"),
    )
    op.create_index(
        "idx_metric_snapshots_connection_date",
        "metric_snapshots",
        ["connection_id", "date"],
        unique=False,
    )
    op.create_index(
        "idx_metric_snapshots_connection_level",
        "metric_snapshots",
        ["connection_id", "level"],
        unique=False,
    )
    op.create_index(
        "idx_metric_snapshots_connection_date_desc",
        "metric_snapshots",
        ["connection_id", sa.text("date DESC")],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_metric_snapshots_connection_date_desc", table_name="metric_snapshots")
    op.drop_index("idx_metric_snapshots_connection_level", table_name="metric_snapshots")
    op.drop_index("idx_metric_snapshots_connection_date", table_name="metric_snapshots")
    op.drop_index("uq_metric_connection_ad", table_name="metric_snapshots")
    op.drop_index("uq_metric_connection_ad_group", table_name="metric_snapshots")
