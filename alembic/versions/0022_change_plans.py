"""change plans

Revision ID: 0022_change_plans
Revises: 0021_org_recommendations
Create Date: 2023-10-28 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0022_change_plans'
down_revision = '0021_org_recommendations'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Change Plans
    op.create_table('change_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='draft', nullable=False),
        sa.Column('date_from', sa.Date(), nullable=True),
        sa.Column('date_to', sa.Date(), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('meta_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.ForeignKeyConstraint(['connection_id'], ['connections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_change_plans_org_created', 'change_plans', ['organization_id', sa.text('created_at DESC')], unique=False)

    # 2. Change Plan Items
    op.create_table('change_plan_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('subject_type', sa.String(length=50), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('params_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['plan_id'], ['change_plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_change_plan_items_plan_status', 'change_plan_items', ['plan_id', 'status'], unique=False)

    # 3. Desired fields in catalog
    op.add_column('ad_campaigns', sa.Column('desired_status', sa.String(length=50), nullable=True))
    op.add_column('ad_campaigns', sa.Column('desired_daily_budget', sa.Numeric(precision=14, scale=2), nullable=True))

    op.add_column('ad_ads', sa.Column('desired_url', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('ad_ads', 'desired_url')
    op.drop_column('ad_campaigns', 'desired_daily_budget')
    op.drop_column('ad_campaigns', 'desired_status')
    op.drop_table('change_plan_items')
    op.drop_table('change_plans')
