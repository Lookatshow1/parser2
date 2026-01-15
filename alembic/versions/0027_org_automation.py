"""org automation settings and runs

Revision ID: 0027_org_automation
Revises: 0026_utm_rules_and_ad_urls
Create Date: 2026-01-14 18:30:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0027_org_automation"
down_revision = "0026_utm_rules_and_ad_urls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "org_automation_settings",
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("run_interval_minutes", sa.Integer(), nullable=False, server_default=sa.text("1440")),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "org_automation_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("error_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_org_automation_runs_org_created", "org_automation_runs", ["organization_id", "created_at"])

    op.create_table(
        "org_automation_actions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("org_automation_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("recommendation_id", sa.Integer(), sa.ForeignKey("org_recommendations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_org_automation_actions_org_status", "org_automation_actions", ["organization_id", "status"])
    op.create_index("idx_org_automation_actions_org_created", "org_automation_actions", ["organization_id", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_org_automation_actions_org_created", table_name="org_automation_actions")
    op.drop_index("idx_org_automation_actions_org_status", table_name="org_automation_actions")
    op.drop_table("org_automation_actions")

    op.drop_index("idx_org_automation_runs_org_created", table_name="org_automation_runs")
    op.drop_table("org_automation_runs")

    op.drop_table("org_automation_settings")
