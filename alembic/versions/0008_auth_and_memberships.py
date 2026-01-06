"""auth users and memberships

Revision ID: 0008_auth_and_memberships
Revises: 0007_metric_snapshot_connection_indexes
Create Date: 2026-01-06 16:20:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_auth_and_memberships"
down_revision = "0007_metric_snapshot_connection_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("active_organization_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_users_active_org",
        "users",
        "organizations",
        ["active_organization_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("idx_org_members_user_id", "organization_members", ["user_id"], unique=False)
    op.create_index("idx_org_members_org_id", "organization_members", ["organization_id"], unique=False)

    op.create_index(
        "idx_connections_org_created_at",
        "connections",
        ["organization_id", sa.text("created_at DESC")],
        unique=False,
    )
    op.create_index(
        "idx_sync_runs_org_created_at",
        "sync_runs",
        ["organization_id", sa.text("created_at DESC")],
        unique=False,
    )
    op.create_index(
        "idx_job_runs_org_created_at",
        "job_runs",
        ["organization_id", sa.text("created_at DESC")],
        unique=False,
    )
    op.create_index(
        "idx_metric_snapshots_org_date",
        "metric_snapshots",
        ["organization_id", "date"],
        unique=False,
    )
    op.create_index(
        "idx_erir_tokens_org_created_at",
        "erir_tokens",
        ["organization_id", sa.text("created_at DESC")],
        unique=False,
    )
    op.create_index(
        "idx_erir_events_org_created_at",
        "erir_events",
        ["organization_id", sa.text("created_at DESC")],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_erir_events_org_created_at", table_name="erir_events")
    op.drop_index("idx_erir_tokens_org_created_at", table_name="erir_tokens")
    op.drop_index("idx_metric_snapshots_org_date", table_name="metric_snapshots")
    op.drop_index("idx_job_runs_org_created_at", table_name="job_runs")
    op.drop_index("idx_sync_runs_org_created_at", table_name="sync_runs")
    op.drop_index("idx_connections_org_created_at", table_name="connections")
    op.drop_index("idx_org_members_org_id", table_name="organization_members")
    op.drop_index("idx_org_members_user_id", table_name="organization_members")
    op.drop_constraint("fk_users_active_org", "users", type_="foreignkey")
    op.drop_column("users", "active_organization_id")
