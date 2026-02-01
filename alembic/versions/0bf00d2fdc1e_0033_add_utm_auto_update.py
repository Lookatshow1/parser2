"""0033_add_utm_auto_update

Revision ID: 0bf00d2fdc1e
Revises: 0032_add_auto_apply
Create Date: 2026-02-01 12:54:37.777728

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0bf00d2fdc1e'
down_revision = '0032_add_auto_apply'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('org_utm_settings')]
    if 'auto_update_ads' not in columns:
        op.add_column('org_utm_settings', sa.Column('auto_update_ads', sa.Boolean(), server_default='0', nullable=False))


def downgrade() -> None:
    op.drop_column('org_utm_settings', 'auto_update_ads')
