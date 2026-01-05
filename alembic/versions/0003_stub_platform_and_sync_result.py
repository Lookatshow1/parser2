"""add stub platform and sync run result

Revision ID: 0003_stub_platform_and_sync_result
Revises: 0002_connection_sync_and_job_run_links
Create Date: 2026-01-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0003_stub_platform_and_sync_result"
down_revision = "0002_connection_sync_and_job_run_links"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_enum
                WHERE enumlabel = 'stub'
                AND enumtypid = 'platform_enum'::regtype
            ) THEN
                ALTER TYPE platform_enum ADD VALUE 'stub';
            END IF;
        END
        $$;
        """
    )

    op.add_column("sync_runs", sa.Column("result_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column("sync_runs", "result_json")
