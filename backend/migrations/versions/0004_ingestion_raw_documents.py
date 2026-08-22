"""ingestion runs and raw documents

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-22
"""
import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("source_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="running"),
        sa.Column("pages_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("documents_stored", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('running','success','partial','failed','cancelled')", name="ck_ingestion_runs_status"),
    )

    op.create_table(
        "raw_documents",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("source_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("opportunity_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("ingestion_run_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("ingestion_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("doc_type", sa.String(20), nullable=False),
        sa.Column("file_url", sa.Text(), nullable=False),
        sa.Column("file_mime", sa.String(100), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("checksum", sa.String(255), unique=True, nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("ocr_used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("vision_used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("meta", sa.dialects.postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("doc_type IN ('HTML','PDF','IMAGE','OTHER')", name="ck_raw_documents_type"),
    )


def downgrade() -> None:
    op.drop_table("raw_documents")
    op.drop_table("ingestion_runs")
