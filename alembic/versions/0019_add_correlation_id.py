"""add correlation id

Revision ID: 0019_add_correlation_id
Revises: 0018_ad_catalog_tables
Create Date: 2023-10-28 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0019_add_correlation_id'
down_revision = '0018_ad_catalog_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('job_runs', sa.Column('correlation_id', sa.String(length=64), nullable=True))
    op.create_index('idx_job_runs_correlation_id', 'job_runs', ['correlation_id'], unique=False)

    op.add_column('sync_runs', sa.Column('correlation_id', sa.String(length=64), nullable=True))
    op.create_index('idx_sync_runs_correlation_id', 'sync_runs', ['correlation_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_sync_runs_correlation_id', table_name='sync_runs')
    op.drop_column('sync_runs', 'correlation_id')

    op.drop_index('idx_job_runs_correlation_id', table_name='job_runs')
    op.drop_column('job_runs', 'correlation_id')
