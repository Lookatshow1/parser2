"""ad catalog tables

Revision ID: 0018_ad_catalog_tables
Revises: 0017_add_builder_tables
Create Date: 2023-10-28 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0018_ad_catalog_tables'
down_revision = '0017_add_builder_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Ad Campaigns
    op.create_table('ad_campaigns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.Enum('yandex', 'ozon', 'vk', 'stub', name='platform_enum'), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['connection_id'], ['connections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('connection_id', 'external_id', name='uq_ad_campaigns')
    )
    op.create_index('idx_ad_campaigns_org', 'ad_campaigns', ['organization_id'], unique=False)

    # 2. Ad Groups
    op.create_table('ad_ad_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.Enum('yandex', 'ozon', 'vk', 'stub', name='platform_enum'), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=False),
        sa.Column('campaign_external_id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['connection_id'], ['connections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('connection_id', 'external_id', name='uq_ad_ad_groups')
    )
    op.create_index('idx_ad_ad_groups_campaign', 'ad_ad_groups', ['connection_id', 'campaign_external_id'], unique=False)

    # 3. Ads
    op.create_table('ad_ads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.Enum('yandex', 'ozon', 'vk', 'stub', name='platform_enum'), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=False),
        sa.Column('ad_group_external_id', sa.String(length=255), nullable=False),
        sa.Column('campaign_external_id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['connection_id'], ['connections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('connection_id', 'external_id', name='uq_ad_ads')
    )
    op.create_index('idx_ad_ads_group', 'ad_ads', ['connection_id', 'ad_group_external_id'], unique=False)

    # 4. Org UTM Settings
    op.create_table('org_utm_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('utm_source', sa.String(length=255), server_default='{platform}', nullable=False),
        sa.Column('utm_medium', sa.String(length=255), server_default='cpc', nullable=False),
        sa.Column('utm_campaign_tpl', sa.String(length=255), server_default='{campaign_id}', nullable=False),
        sa.Column('utm_content_tpl', sa.String(length=255), server_default='{ad_id}', nullable=False),
        sa.Column('utm_term_tpl', sa.String(length=255), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', name='uq_org_utm_settings')
    )


def downgrade() -> None:
    op.drop_table('org_utm_settings')
    op.drop_table('ad_ads')
    op.drop_table('ad_ad_groups')
    op.drop_table('ad_campaigns')
