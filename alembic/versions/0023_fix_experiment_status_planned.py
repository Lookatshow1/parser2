"""fix experiment status planned

Revision ID: 0023_fix_experiment_status_planned
Revises: 0022_change_plans
Create Date: 2026-01-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0023_fix_experiment_status_planned'
down_revision = '0022_change_plans'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update all experiments with status 'planned' to 'draft'
    # Since 'planned' is not in the enum, we need to use raw SQL
    op.execute("""
        UPDATE experiments 
        SET status = 'draft'::experiment_status_enum 
        WHERE status::text = 'planned'
    """)


def downgrade() -> None:
    # Cannot restore 'planned' status since it's not in the enum
    # This is a one-way migration
    pass
