"""add auto_apply to org_automation_settings

Revision ID: 0032_add_auto_apply
Revises: 0031_add_erid
Create Date: 2026-02-01
"""
from alembic import op
import sqlalchemy as sa


revision = '0032_add_auto_apply'
down_revision = '0031_add_erid'
branch_labels = None
depends_on = None


def upgrade():
    # Add auto_apply column to org_automation_settings
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('org_automation_settings')]
    if 'auto_apply' not in columns:
        op.add_column(
            'org_automation_settings',
            sa.Column('auto_apply', sa.Boolean(), server_default=sa.text('false'), nullable=False)
        )


def downgrade():
    op.drop_column('org_automation_settings', 'auto_apply')
