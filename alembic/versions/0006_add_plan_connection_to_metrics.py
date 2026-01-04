"""add plan connection to metrics

Revision ID: 0006_add_plan_connection
Revises: 991e7971e174
Create Date: 2026-01-04 14:36:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0006_add_plan_connection"
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

    # Дедупликация: удаляем дубликаты, оставляем запись с максимальным id
    # Делаем только для строк где connection_id и plan_id не NULL
    op.execute("""
        DELETE FROM metric_snapshots
        WHERE id IN (
            SELECT id
            FROM (
                SELECT id,
                       ROW_NUMBER() OVER (
                           PARTITION BY connection_id, plan_id, date, campaign_external_id
                           ORDER BY id DESC
                       ) as rn
                FROM metric_snapshots
                WHERE connection_id IS NOT NULL
                  AND plan_id IS NOT NULL
            ) t
            WHERE rn > 1
        )
    """)

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

