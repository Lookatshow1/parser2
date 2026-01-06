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
    op.execute("ALTER TYPE job_status_enum RENAME VALUE 'queued' TO 'pending'")
    op.execute("ALTER TYPE job_status_enum RENAME VALUE 'succeeded' TO 'success'")


def downgrade() -> None:
    op.execute("ALTER TYPE job_status_enum RENAME VALUE 'success' TO 'succeeded'")
    op.execute("ALTER TYPE job_status_enum RENAME VALUE 'pending' TO 'queued'")
