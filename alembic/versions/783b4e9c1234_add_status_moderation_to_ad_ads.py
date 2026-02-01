"""Add status and moderation_status to ad_ads

Revision ID: 783b4e9c1234
Revises: 68d5943d632e
Create Date: 2026-02-01 23:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '783b4e9c1234'
down_revision = '0bf00d2fdc1e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add status column to track ad state (active, paused, archived)
    op.add_column('ad_ads', sa.Column('status', sa.String(50), nullable=True))
    
    # Add moderation_status column to track moderation state (approved, rejected, pending)
    op.add_column('ad_ads', sa.Column('moderation_status', sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column('ad_ads', 'moderation_status')
    op.drop_column('ad_ads', 'status')
