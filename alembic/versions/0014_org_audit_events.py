"""org audit events

Revision ID: 0014_org_audit_events
Revises: 0013_org_invites_revoked_fields
Create Date: 2026-01-08 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0014_org_audit_events"
down_revision = "0013_org_invites_revoked_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "org_audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("subject_type", sa.String(length=50), nullable=True),
        sa.Column("subject_id", sa.Integer(), nullable=True),
        sa.Column(
            "meta",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
    )
    op.create_index(
        "idx_org_audit_org_created_at",
        "org_audit_events",
        ["organization_id", sa.text("created_at DESC")],
        unique=False,
    )
    op.create_index(
        "idx_org_audit_org_action",
        "org_audit_events",
        ["organization_id", "action"],
        unique=False,
    )
    op.create_index(
        "idx_org_audit_subject",
        "org_audit_events",
        ["subject_type", "subject_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_org_audit_subject", table_name="org_audit_events")
    op.drop_index("idx_org_audit_org_action", table_name="org_audit_events")
    op.drop_index("idx_org_audit_org_created_at", table_name="org_audit_events")
    op.drop_table("org_audit_events")
