"""experiment rounds and hypotheses

Revision ID: 0005_experiment_rounds_hypotheses
Revises: 0004_creative_compliance_token
Create Date: 2024-01-05 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_experiment_rounds_hypotheses"

down_revision = "0004_creative_compliance_token"

branch_labels = None

depends_on = None


hypothesis_status_enum = sa.Enum("draft", "active", "completed", name="hypothesisstatus")


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("advertiser_id", sa.Integer(), sa.ForeignKey("advertisers.id"), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.add_column("experiments", sa.Column("project_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_experiments_project",
        "experiments",
        "projects",
        ["project_id"],
        ["id"],
    )
    op.add_column("experiments", sa.Column("total_budget", sa.Integer(), nullable=True))
    op.add_column("experiments", sa.Column("platforms", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("experiments", sa.Column("processing", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("experiments", sa.Column("started_at", sa.DateTime(), nullable=True))
    op.add_column("experiments", sa.Column("ended_at", sa.DateTime(), nullable=True))
    op.alter_column("experiments", "plan_id", existing_type=sa.Integer(), nullable=True)

    op.create_table(
        "experiment_rounds",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("experiment_id", sa.Integer(), sa.ForeignKey("experiments.id"), nullable=False),
        sa.Column("round_index", sa.Integer(), nullable=False),
        sa.Column("budget_plan", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("experiment_id", "round_index", name="uq_round_index"),
    )

    hypothesis_status_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "hypotheses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "experiment_round_id",
            sa.Integer(),
            sa.ForeignKey("experiment_rounds.id"),
            nullable=False,
        ),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("segmentation_params", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", hypothesis_status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.add_column("creative_variants", sa.Column("hypothesis_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_creative_variants_hypothesis",
        "creative_variants",
        "hypotheses",
        ["hypothesis_id"],
        ["id"],
    )
    op.add_column("creative_variants", sa.Column("title", sa.String(length=255), nullable=True))
    op.add_column("creative_variants", sa.Column("media_url", sa.String(length=2048), nullable=True))
    op.add_column("creative_variants", sa.Column("moderation_status", sa.String(length=64), nullable=True))
    op.add_column("creative_variants", sa.Column("external_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    op.add_column("budget_allocations", sa.Column("experiment_round_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_budget_allocations_round",
        "budget_allocations",
        "experiment_rounds",
        ["experiment_round_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_budget_allocations_round", "budget_allocations", type_="foreignkey")
    op.drop_column("budget_allocations", "experiment_round_id")

    op.drop_column("creative_variants", "external_ids")
    op.drop_column("creative_variants", "moderation_status")
    op.drop_column("creative_variants", "media_url")
    op.drop_column("creative_variants", "title")
    op.drop_constraint("fk_creative_variants_hypothesis", "creative_variants", type_="foreignkey")
    op.drop_column("creative_variants", "hypothesis_id")

    op.drop_table("hypotheses")
    hypothesis_status_enum.drop(op.get_bind(), checkfirst=True)

    op.drop_table("experiment_rounds")

    op.drop_column("experiments", "ended_at")
    op.drop_column("experiments", "started_at")
    op.drop_column("experiments", "processing")
    op.drop_column("experiments", "platforms")
    op.drop_column("experiments", "total_budget")
    op.drop_constraint("fk_experiments_project", "experiments", type_="foreignkey")
    op.drop_column("experiments", "project_id")
    op.alter_column("experiments", "plan_id", existing_type=sa.Integer(), nullable=False)

    op.drop_table("projects")
