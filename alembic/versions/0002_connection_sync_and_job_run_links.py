"""connection sync + job run links

Revision ID: 0002_connection_sync_and_job_run_links
Revises: 0001_init_complete
Create Date: 2026-01-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0002_connection_sync_and_job_run_links"
down_revision = "0001_init_complete"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("job_runs", sa.Column("organization_id", sa.Integer(), nullable=True))
    op.add_column("job_runs", sa.Column("connection_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_job_runs_organization_id",
        "job_runs",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_job_runs_connection_id",
        "job_runs",
        "connections",
        ["connection_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("idx_job_runs_organization_id", "job_runs", ["organization_id"], unique=False)
    op.create_index("idx_job_runs_connection_id", "job_runs", ["connection_id"], unique=False)

    op.add_column("sync_runs", sa.Column("connection_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_sync_runs_connection_id",
        "sync_runs",
        "connections",
        ["connection_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.alter_column("sync_runs", "experiment_id", existing_type=sa.Integer(), nullable=True)
    op.create_index(
        "idx_sync_runs_connection_created_at",
        "sync_runs",
        ["connection_id", sa.text("created_at DESC")],
        unique=False,
    )

    op.create_index(
        "uq_metric_connection_campaign",
        "metric_snapshots",
        ["organization_id", "connection_id", "platform", "date", "campaign_external_id"],
        unique=True,
        postgresql_where=sa.text("level = 'campaign' AND connection_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_metric_connection_campaign", table_name="metric_snapshots")

    op.drop_index("idx_sync_runs_connection_created_at", table_name="sync_runs")
    op.alter_column("sync_runs", "experiment_id", existing_type=sa.Integer(), nullable=False)
    op.drop_constraint("fk_sync_runs_connection_id", "sync_runs", type_="foreignkey")
    op.drop_column("sync_runs", "connection_id")

    op.drop_index("idx_job_runs_connection_id", table_name="job_runs")
    op.drop_index("idx_job_runs_organization_id", table_name="job_runs")
    op.drop_constraint("fk_job_runs_connection_id", "job_runs", type_="foreignkey")
    op.drop_constraint("fk_job_runs_organization_id", "job_runs", type_="foreignkey")
    op.drop_column("job_runs", "connection_id")
    op.drop_column("job_runs", "organization_id")
