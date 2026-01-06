"""init complete

Revision ID: 0001_init_complete
Revises:
Create Date: 2023-10-28 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001_init_complete'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Alembic creates alembic_version with VARCHAR(32); widen for long revision ids.
    op.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(128)")
    # 1. Enums (create if not exists logic is tricky in pure alembic without raw sql check,
    # but since it's init, we assume clean DB)
    # We use sa.Enum with native_enum=True (default for postgres)

    # 2. Organizations & Users
    op.create_table('organizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Default org
    op.execute("INSERT INTO organizations (name) VALUES ('Dev Org')")

    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    op.create_table('organization_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False), # owner, admin, analyst, viewer
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'user_id', name='uq_org_member')
    )

    # 3. Advertisers
    op.create_table('advertisers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. Projects
    op.create_table('projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('advertiser_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['advertiser_id'], ['advertisers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. Connections
    op.create_table('connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False), # Backfilled later? No, new table.
        sa.Column('advertiser_id', sa.Integer(), nullable=True),
        sa.Column('platform', sa.Enum('yandex', 'ozon', 'vk', 'stub', name='platform_enum'), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('credentials_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('credentials_encrypted', postgresql.BYTEA(), nullable=True),
        sa.Column('credentials_version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('status', sa.Enum('active', 'inactive', 'error', name='connection_status_enum', native_enum=False), server_default='active', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['advertiser_id'], ['advertisers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_connections_platform', 'connections', ['platform'], unique=False)

    # 6. Campaign Plans
    op.create_table('campaign_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('advertiser_id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('platform', sa.Enum('yandex', 'ozon', 'vk', 'stub', name='platform_enum'), nullable=False),
        sa.Column('budget', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('currency', sa.String(length=10), server_default='RUB', nullable=False),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('internal_code', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['advertiser_id'], ['advertisers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['connection_id'], ['connections.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_plans_connection_id', 'campaign_plans', ['connection_id'], unique=False)

    # 7. Experiments
    op.create_table('experiments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('total_budget', sa.Integer(), nullable=True),
        sa.Column('platforms', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('processing', sa.Boolean(), nullable=False),
        sa.Column('status', sa.Enum('draft', 'running', 'stopped', 'completed', name='experiment_status_enum'), nullable=False),
        sa.Column('start_at', sa.DateTime(), nullable=True),
        sa.Column('end_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['plan_id'], ['campaign_plans.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 8. Experiment Rounds
    op.create_table('experiment_rounds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('experiment_id', sa.Integer(), nullable=False),
        sa.Column('round_index', sa.Integer(), nullable=False),
        sa.Column('budget_plan', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('experiment_id', 'round_index', name='uq_round_index')
    )

    # 9. Hypotheses
    op.create_table('hypotheses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('experiment_round_id', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('segmentation_params', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.Enum('draft', 'active', 'completed', 'rejected', name='hypothesis_status_enum'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['experiment_round_id'], ['experiment_rounds.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 10. Creative Variants
    op.create_table('creative_variants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('experiment_id', sa.Integer(), nullable=False),
        sa.Column('hypothesis_id', sa.Integer(), nullable=True),
        sa.Column('platform', sa.Enum('yandex', 'ozon', 'vk', 'stub', name='platform_enum'), nullable=False),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('image_url', sa.String(length=2048), nullable=True),
        sa.Column('media_url', sa.String(length=2048), nullable=True),
        sa.Column('meta_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('moderation_status', sa.String(length=64), nullable=True),
        sa.Column('external_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('compliance_token', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ),
        sa.ForeignKeyConstraint(['hypothesis_id'], ['hypotheses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 11. Budget Allocations
    op.create_table('budget_allocations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('experiment_id', sa.Integer(), nullable=False),
        sa.Column('experiment_round_id', sa.Integer(), nullable=True),
        sa.Column('platform', sa.Enum('yandex', 'ozon', 'vk', 'stub', name='platform_enum'), nullable=False),
        sa.Column('creative_variant_id', sa.Integer(), nullable=True),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['creative_variant_id'], ['creative_variants.id'], ),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ),
        sa.ForeignKeyConstraint(['experiment_round_id'], ['experiment_rounds.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 12. OAuth States
    op.create_table('oauth_states',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('state', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=True),
        sa.Column('error_text', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['connection_id'], ['connections.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('state')
    )

    # 13. Job Runs
    op.create_table('job_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_type', sa.String(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'running', 'success', 'failed', 'canceled', name='job_status_enum'), nullable=False),
        sa.Column('context_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('result_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_text', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_job_runs_status', 'job_runs', ['status'], unique=False)
    op.create_index('idx_job_runs_created_at_desc', 'job_runs', [sa.text('created_at DESC')], unique=False)

    # 14. Sync Runs
    op.create_table('sync_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('experiment_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.Enum('yandex', 'ozon', 'vk', 'stub', name='platform_enum'), nullable=False),
        sa.Column('run_type', sa.Enum('campaigns', 'metrics', 'full', name='sync_run_type_enum', native_enum=False), nullable=False),
        sa.Column('status', sa.Enum('queued', 'running', 'success', 'failed', 'canceled', name='sync_run_status_enum', native_enum=False), nullable=False),
        sa.Column('params_json', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_text', sa.Text(), nullable=True),
        sa.Column('has_warnings', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_sync_runs_experiment_platform_created_at', 'sync_runs', ['experiment_id', 'platform', sa.text('created_at DESC')], unique=False)

    # 15. Sync Events
    op.create_table('sync_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sync_run_id', sa.Integer(), nullable=False),
        sa.Column('level', sa.String(length=20), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('payload_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['sync_run_id'], ['sync_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_sync_events_run_created_at', 'sync_events', ['sync_run_id', sa.text('created_at DESC')], unique=False)

    # 16. Experiment Campaigns
    op.create_table('experiment_campaigns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('experiment_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.Enum('yandex', 'ozon', 'vk', 'stub', name='platform_enum'), nullable=False),
        sa.Column('campaign_external_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('experiment_id', 'platform', 'campaign_external_id', name='uq_experiment_campaign')
    )

    # 17. Experiment Ad Groups
    op.create_table('experiment_ad_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('experiment_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.Enum('yandex', 'ozon', 'vk', 'stub', name='platform_enum'), nullable=False),
        sa.Column('campaign_external_id', sa.String(), nullable=False),
        sa.Column('ad_group_external_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('payload_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'experiment_id', 'platform', 'ad_group_external_id', name='uq_experiment_ad_groups')
    )

    # 18. Experiment Ads
    op.create_table('experiment_ads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('experiment_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.Enum('yandex', 'ozon', 'vk', 'stub', name='platform_enum'), nullable=False),
        sa.Column('campaign_external_id', sa.String(), nullable=False),
        sa.Column('ad_group_external_id', sa.String(), nullable=False),
        sa.Column('ad_external_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('destination_url', sa.String(), nullable=True),
        sa.Column('preview_url', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('payload_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'experiment_id', 'platform', 'ad_external_id', name='uq_experiment_ads')
    )

    # 19. Ad Creatives
    op.create_table('ad_creatives',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('experiment_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.Enum('yandex', 'ozon', 'vk', 'stub', name='platform_enum'), nullable=False),
        sa.Column('creative_external_id', sa.String(), nullable=False),
        sa.Column('ad_external_id', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('preview_url', sa.String(), nullable=True),
        sa.Column('payload_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'experiment_id', 'platform', 'creative_external_id', name='uq_ad_creatives')
    )

    # 20. Erir Tokens
    op.create_table('erir_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('experiment_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.Enum('yandex', 'ozon', 'vk', name='platform_enum'), nullable=False),
        sa.Column('creative_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(), nullable=True),
        sa.Column('token_status', sa.String(length=50), nullable=False),
        sa.Column('issued_at', sa.DateTime(), nullable=True),
        sa.Column('error_text', sa.Text(), nullable=True),
        sa.Column('request_payload_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('response_payload_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['creative_id'], ['ad_creatives.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'creative_id', name='uq_erir_token')
    )
    op.create_index('idx_erir_tokens_status', 'erir_tokens', ['token_status'], unique=False)

    # 21. Erir Events
    op.create_table('erir_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('experiment_id', sa.Integer(), nullable=True),
        sa.Column('erir_token_id', sa.Integer(), nullable=True),
        sa.Column('level', sa.String(length=20), nullable=True),
        sa.Column('code', sa.String(length=100), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('payload_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['erir_token_id'], ['erir_tokens.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_erir_events_token_created_at', 'erir_events', ['erir_token_id', sa.text('created_at DESC')], unique=False)

    # 22. Metric Snapshots
    op.create_table('metric_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=True),
        sa.Column('plan_id', sa.Integer(), nullable=True),
        sa.Column('experiment_id', sa.Integer(), nullable=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('platform', sa.Enum('yandex', 'ozon', 'vk', name='platform_enum'), nullable=False),
        sa.Column('level', sa.String(), server_default='campaign', nullable=False),
        sa.Column('campaign_external_id', sa.String(length=255), nullable=False),
        sa.Column('ad_group_external_id', sa.String(), nullable=True),
        sa.Column('ad_external_id', sa.String(), nullable=True),
        sa.Column('clicks', sa.Integer(), nullable=False),
        sa.Column('impressions', sa.Integer(), nullable=False),
        sa.Column('spend', sa.Integer(), nullable=False),
        sa.Column('leads', sa.Integer(), nullable=False),
        sa.Column('purchases', sa.Integer(), nullable=False),
        sa.Column('revenue', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['connection_id'], ['connections.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['plan_id'], ['campaign_plans.id'], ),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_metric_snapshots_campaign', 'metric_snapshots', ['campaign_external_id'], unique=False)
    op.create_index('idx_metric_snapshots_experiment_platform_date', 'metric_snapshots', ['experiment_id', 'platform', 'date'], unique=False)

    # Partial unique indexes
    op.create_index('uq_metric_campaign', 'metric_snapshots', ['organization_id', 'experiment_id', 'platform', 'date', 'campaign_external_id'], unique=True, postgresql_where=sa.text("level = 'campaign'"))
    op.create_index('uq_metric_ad_group', 'metric_snapshots', ['organization_id', 'experiment_id', 'platform', 'date', 'campaign_external_id', 'ad_group_external_id'], unique=True, postgresql_where=sa.text("level = 'ad_group'"))
    op.create_index('uq_metric_ad', 'metric_snapshots', ['organization_id', 'experiment_id', 'platform', 'date', 'campaign_external_id', 'ad_group_external_id', 'ad_external_id'], unique=True, postgresql_where=sa.text("level = 'ad'"))

    # 23. Conversion Events
    op.create_table('conversion_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.String(length=36), nullable=False),
        sa.Column('event_type', sa.Enum('lead', 'purchase', name='conversioneventtype'), nullable=False),
        sa.Column('occurred_at', sa.DateTime(), nullable=False),
        sa.Column('landing_url', sa.String(length=2048), nullable=False),
        sa.Column('utm_source', sa.String(length=255), nullable=True),
        sa.Column('utm_medium', sa.String(length=255), nullable=True),
        sa.Column('utm_campaign', sa.String(length=255), nullable=True),
        sa.Column('utm_content', sa.String(length=255), nullable=True),
        sa.Column('utm_term', sa.String(length=255), nullable=True),
        sa.Column('contact_phone', sa.String(length=64), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('value', sa.Integer(), nullable=True),
        sa.Column('plan_id', sa.Integer(), nullable=True),
        sa.Column('experiment_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ),
        sa.ForeignKeyConstraint(['plan_id'], ['campaign_plans.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id')
    )


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_table('conversion_events')
    op.drop_table('metric_snapshots')
    op.drop_table('erir_events')
    op.drop_table('erir_tokens')
    op.drop_table('ad_creatives')
    op.drop_table('experiment_ads')
    op.drop_table('experiment_ad_groups')
    op.drop_table('experiment_campaigns')
    op.drop_table('sync_events')
    op.drop_table('sync_runs')
    op.drop_table('job_runs')
    op.drop_table('oauth_states')
    op.drop_table('budget_allocations')
    op.drop_table('creative_variants')
    op.drop_table('hypotheses')
    op.drop_table('experiment_rounds')
    op.drop_table('experiments')
    op.drop_table('campaign_plans')
    op.drop_table('connections')
    op.drop_table('projects')
    op.drop_table('advertisers')
    op.drop_table('organization_members')
    op.drop_table('users')
    op.drop_table('organizations')

    op.execute("DROP TYPE IF EXISTS platform_enum")
    op.execute("DROP TYPE IF EXISTS experiment_status_enum")
    op.execute("DROP TYPE IF EXISTS hypothesis_status_enum")
    op.execute("DROP TYPE IF EXISTS job_status_enum")
    op.execute("DROP TYPE IF EXISTS conversioneventtype")
