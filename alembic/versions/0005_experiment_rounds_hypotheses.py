"""experiment rounds hypotheses

Revision ID: 0005_experiment_rounds_hyp
Revises: 0004_creative_compliance_token
Create Date: 2025-12-30 21:54:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0005_experiment_rounds_hyp"
down_revision: Union[str, None] = "0004_creative_compliance_token"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    op.add_column("experiments", sa.Column("project_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_experiments_project_id_projects",
        "experiments",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="SET NULL",
    )

    experiment_round_status_enum = postgresql.ENUM(
        "planned",
        "running",
        "paused",
        "completed",
        name="experiment_round_status_enum",
        create_type=False,
    )
    experiment_round_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "experiment_rounds",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "experiment_id",
            sa.Integer(),
            sa.ForeignKey("experiments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", experiment_round_status_enum, nullable=False, server_default="planned"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metrics_json", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    hypothesis_status_enum = postgresql.ENUM(
        "draft",
        "active",
        "done",
        "rejected",
        name="hypothesis_status_enum",
        create_type=False,
    )
    hypothesis_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "hypotheses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "experiment_round_id",
            sa.Integer(),
            sa.ForeignKey("experiment_rounds.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", hypothesis_status_enum, nullable=False, server_default="draft"),
        sa.Column("assumptions_json", postgresql.JSONB(), nullable=True),
        sa.Column("expected_impact", sa.String(length=255), nullable=True),
        sa.Column("metrics_json", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    op.add_column(
        "creative_variants",
        sa.Column("experiment_round_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "creative_variants",
        sa.Column("hypothesis_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_creative_variants_experiment_round_id_experiment_rounds",
        "creative_variants",
        "experiment_rounds",
        ["experiment_round_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_creative_variants_hypothesis_id_hypotheses",
        "creative_variants",
        "hypotheses",
        ["hypothesis_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_creative_variants_hypothesis_id_hypotheses",
        "creative_variants",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_creative_variants_experiment_round_id_experiment_rounds",
        "creative_variants",
        type_="foreignkey",
    )
    op.drop_column("creative_variants", "hypothesis_id")
    op.drop_column("creative_variants", "experiment_round_id")

    op.drop_table("hypotheses")
    op.drop_table("experiment_rounds")

    op.execute("DROP TYPE IF EXISTS hypothesis_status_enum")
    op.execute("DROP TYPE IF EXISTS experiment_round_status_enum")

    op.drop_constraint(
        "fk_experiments_project_id_projects",
        "experiments",
        type_="foreignkey",
    )
    op.drop_column("experiments", "project_id")

    op.drop_table("projects")
