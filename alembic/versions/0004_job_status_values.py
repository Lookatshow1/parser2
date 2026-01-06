"""rename job status enum values

Revision ID: 0004_job_status_values
Revises: 0003_stub_platform_and_sync_result
Create Date: 2026-01-06 00:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "0004_job_status_values"
down_revision = "0003_stub_platform_and_sync_result"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1
            FROM pg_enum e
            JOIN pg_type t ON t.oid = e.enumtypid
            WHERE t.typname = 'job_status_enum' AND e.enumlabel = 'queued'
          ) THEN
            ALTER TYPE job_status_enum RENAME VALUE 'queued' TO 'pending';
          END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1
            FROM pg_enum e
            JOIN pg_type t ON t.oid = e.enumtypid
            WHERE t.typname = 'job_status_enum' AND e.enumlabel = 'succeeded'
          ) THEN
            ALTER TYPE job_status_enum RENAME VALUE 'succeeded' TO 'success';
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1
            FROM pg_enum e
            JOIN pg_type t ON t.oid = e.enumtypid
            WHERE t.typname = 'job_status_enum' AND e.enumlabel = 'success'
          ) THEN
            ALTER TYPE job_status_enum RENAME VALUE 'success' TO 'succeeded';
          END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1
            FROM pg_enum e
            JOIN pg_type t ON t.oid = e.enumtypid
            WHERE t.typname = 'job_status_enum' AND e.enumlabel = 'pending'
          ) THEN
            ALTER TYPE job_status_enum RENAME VALUE 'pending' TO 'queued';
          END IF;
        END $$;
        """
    )
