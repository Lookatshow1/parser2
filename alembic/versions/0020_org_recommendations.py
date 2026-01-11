"""org recommendations

Revision ID: 0020_org_recommendations
Revises: 0019_add_correlation_id
Create Date: 2023-10-28 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0020_org_recommendations'
down_revision = '0019_add_correlation_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('org_recommendations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=True),
        sa.Column('subject_type', sa.String(length=50), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=True),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('action', sa.Text(), nullable=False),
        sa.Column('meta_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('valid_from', sa.Date(), nullable=False),
        sa.Column('valid_to', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by_user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['connection_id'], ['connections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resolved_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'connection_id', 'subject_type', 'subject_id', 'code', 'valid_from', 'valid_to', name='uq_org_recommendations')
    )
    op.create_index('idx_org_recommendations_org_created', 'org_recommendations', ['organization_id', sa.text('created_at DESC')], unique=False)
    op.create_index('idx_org_recommendations_conn_created', 'org_recommendations', ['organization_id', 'connection_id', sa.text('created_at DESC')], unique=False)


def downgrade() -> None:
    op.drop_table('org_recommendations')
