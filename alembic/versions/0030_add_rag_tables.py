"""add rag tables

Revision ID: 0030_add_rag_tables
Revises: 0029_add_planned_status
Create Date: 2026-01-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0030_add_rag_tables"
down_revision = "0029_add_planned_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rag_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("url", sa.String(length=2048), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("meta_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="ready"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_rag_documents_org", "rag_documents", ["organization_id"])
    op.create_index("idx_rag_documents_source", "rag_documents", ["organization_id", "source_type", "source_id"])

    op.create_table(
        "rag_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("rag_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding_json", sa.JSON(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_rag_chunks_org", "rag_chunks", ["organization_id"])
    op.create_index("idx_rag_chunks_doc", "rag_chunks", ["document_id"])


def downgrade() -> None:
    op.drop_index("idx_rag_chunks_doc", table_name="rag_chunks")
    op.drop_index("idx_rag_chunks_org", table_name="rag_chunks")
    op.drop_table("rag_chunks")

    op.drop_index("idx_rag_documents_source", table_name="rag_documents")
    op.drop_index("idx_rag_documents_org", table_name="rag_documents")
    op.drop_table("rag_documents")
