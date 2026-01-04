from alembic import op
import sqlalchemy as sa


revision = "<оставь то что сгенерировал alembic>"
down_revision = "991e7971e174"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("metric_snapshots", sa.Column("plan_id", sa.Integer(), nullable=True))
    op.add_column("metric_snapshots", sa.Column("connection_id", sa.Integer(), nullable=True))

    op.create_foreign_key(
        "fk_metric_snapshots_plan",
        "metric_snapshots",
        "campaign_plans",
        ["plan_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_foreign_key(
        "fk_metric_snapshots_connection",
        "metric_snapshots",
        "connections",
        ["connection_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # уникальность для дедупликации повторных синков
    op.create_unique_constraint(
        "uq_metric_snapshots_conn_plan_date_campaign",
        "metric_snapshots",
        ["connection_id", "plan_id", "date", "campaign_external_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_metric_snapshots_conn_plan_date_campaign", "metric_snapshots", type_="unique")
    op.drop_constraint("fk_metric_snapshots_connection", "metric_snapshots", type_="foreignkey")
    op.drop_constraint("fk_metric_snapshots_plan", "metric_snapshots", type_="foreignkey")
    op.drop_column("metric_snapshots", "connection_id")
    op.drop_column("metric_snapshots", "plan_id")
