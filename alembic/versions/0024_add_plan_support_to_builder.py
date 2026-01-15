"""add plan support to builder

Revision ID: 0024_add_plan_support_to_builder
Revises: 0023_fix_experiment_status_planned
Create Date: 2026-01-04 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0024_add_plan_support_to_builder'
down_revision = '0023_fix_experiment_status_planned'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add status enum to campaign_plans (draft/archived)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE campaign_plan_status_enum AS ENUM ('draft', 'archived');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.add_column('campaign_plans', sa.Column('status', sa.Enum('draft', 'archived', name='campaign_plan_status_enum'), server_default='draft', nullable=False))
    
    # 2. Make experiment_id nullable in builder_campaigns and add plan_id
    op.alter_column('builder_campaigns', 'experiment_id',
                    existing_type=sa.Integer(),
                    nullable=True)
    
    op.add_column('builder_campaigns', sa.Column('plan_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_builder_campaigns_plan', 'builder_campaigns', 'campaign_plans', ['plan_id'], ['id'], ondelete='CASCADE')
    op.create_index('idx_builder_campaigns_plan', 'builder_campaigns', ['plan_id'])
    
    # Add constraint: either experiment_id or plan_id must be set
    op.execute("""
        ALTER TABLE builder_campaigns 
        ADD CONSTRAINT chk_builder_campaigns_experiment_or_plan 
        CHECK ((experiment_id IS NOT NULL) OR (plan_id IS NOT NULL))
    """)
    
    # 3. Add missing fields to builder_campaigns
    op.add_column('builder_campaigns', sa.Column('daily_budget', sa.Numeric(precision=14, scale=2), nullable=True))
    op.add_column('builder_campaigns', sa.Column('total_budget', sa.Numeric(precision=14, scale=2), nullable=True))
    op.add_column('builder_campaigns', sa.Column('goal', sa.String(length=255), nullable=True))
    op.add_column('builder_campaigns', sa.Column('external_ref', sa.String(length=255), nullable=True))
    
    # 4. Add missing fields to builder_ad_groups
    op.add_column('builder_ad_groups', sa.Column('targeting_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False))
    op.add_column('builder_ad_groups', sa.Column('bid', sa.Numeric(precision=14, scale=2), nullable=True))
    op.add_column('builder_ad_groups', sa.Column('plan_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_builder_ad_groups_plan', 'builder_ad_groups', 'campaign_plans', ['plan_id'], ['id'], ondelete='CASCADE')
    op.create_index('idx_builder_ad_groups_plan', 'builder_ad_groups', ['plan_id'])


def downgrade() -> None:
    op.drop_index('idx_builder_ad_groups_plan', table_name='builder_ad_groups')
    op.drop_constraint('fk_builder_ad_groups_plan', 'builder_ad_groups', type_='foreignkey')
    op.drop_column('builder_ad_groups', 'plan_id')
    op.drop_column('builder_ad_groups', 'bid')
    op.drop_column('builder_ad_groups', 'targeting_json')
    
    op.drop_constraint('chk_builder_campaigns_experiment_or_plan', 'builder_campaigns', type_='check')
    op.drop_index('idx_builder_campaigns_plan', table_name='builder_campaigns')
    op.drop_constraint('fk_builder_campaigns_plan', 'builder_campaigns', type_='foreignkey')
    op.drop_column('builder_campaigns', 'external_ref')
    op.drop_column('builder_campaigns', 'goal')
    op.drop_column('builder_campaigns', 'total_budget')
    op.drop_column('builder_campaigns', 'daily_budget')
    op.drop_column('builder_campaigns', 'plan_id')
    
    op.alter_column('builder_campaigns', 'experiment_id',
                    existing_type=sa.Integer(),
                    nullable=False)
    
    op.drop_column('campaign_plans', 'status')
    op.execute("DROP TYPE IF EXISTS campaign_plan_status_enum")
