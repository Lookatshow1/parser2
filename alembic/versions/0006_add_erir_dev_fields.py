"""add erir dev fields

Revision ID: 0006_add_erir_dev_fields
Revises: 0005_metric_snapshots_updated_at
Create Date: 2026-01-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0006_add_erir_dev_fields"
down_revision = "0005_metric_snapshots_updated_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("erir_tokens", sa.Column("provider", sa.String(length=50), nullable=True))
    op.add_column("erir_tokens", sa.Column("token_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("erir_tokens", sa.Column("expires_at", sa.DateTime(), nullable=True))

    op.add_column("erir_events", sa.Column("connection_id", sa.Integer(), nullable=True))
    op.add_column("erir_events", sa.Column("event_type", sa.String(length=50), nullable=True))
    op.add_column(
        "erir_events",
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "running",
                "success",
                "failed",
                "canceled",
                name="erir_status_enum",
                native_enum=False,
            ),
            server_default="pending",
            nullable=False,
        ),
    )
    op.add_column("erir_events", sa.Column("error_text", sa.Text(), nullable=True))
    op.add_column("erir_events", sa.Column("result_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column(
        "erir_events",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_foreign_key(
        "fk_erir_events_connection_id",
        "erir_events",
        "connections",
        ["connection_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_erir_events_connection_id", "erir_events", type_="foreignkey")
    op.drop_column("erir_events", "updated_at")
    op.drop_column("erir_events", "result_json")
    op.drop_column("erir_events", "error_text")
    op.drop_column("erir_events", "status")
    op.drop_column("erir_events", "event_type")
    op.drop_column("erir_events", "connection_id")

    op.drop_column("erir_tokens", "expires_at")
    op.drop_column("erir_tokens", "token_json")
    op.drop_column("erir_tokens", "provider")
