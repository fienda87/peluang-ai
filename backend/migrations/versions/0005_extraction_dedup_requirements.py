"""extraction results, dedup decisions, requirements

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-22
"""
import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "extraction_results",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("raw_document_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("raw_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("opportunity_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("strategy", sa.String(50), nullable=False),
        sa.Column("extracted_data", sa.dialects.postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("field_confidence", sa.dialects.postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("evidence_refs", sa.dialects.postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("overall_confidence", sa.Numeric(5, 2), nullable=False, server_default="0.00"),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "strategy IN ('metadata','dom_css','regex','pdf_text','ocr','vision_llm','llm','manual')",
            name="ck_extraction_results_strategy",
        ),
        sa.CheckConstraint(
            "status IN ('pending','valid','invalid','needs_recovery','recovered','failed')",
            name="ck_extraction_results_status",
        ),
        sa.CheckConstraint("overall_confidence >= 0 AND overall_confidence <= 1.00", name="ck_extraction_results_confidence"),
        sa.UniqueConstraint("raw_document_id", "version", name="uq_extraction_doc_version"),
    )

    op.create_table(
        "dedup_decisions",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("opportunity_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("duplicate_of_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("method", sa.String(50), nullable=False),
        sa.Column("similarity_score", sa.Numeric(5, 4), nullable=True),
        sa.Column("is_duplicate", sa.Boolean(), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "method IN ('checksum','url_canonical','title_date','embedding_similarity','manual')",
            name="ck_dedup_decisions_method",
        ),
        sa.UniqueConstraint("opportunity_id", name="uq_dedup_opportunity"),
    )

    op.create_table(
        "opportunity_requirements",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("opportunity_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("req_type", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("structured", sa.dialects.postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("evidence_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "req_type IN ('gpa','major','education_level','age','location','skill','experience','document','other')",
            name="ck_requirements_type",
        ),
    )


def downgrade() -> None:
    op.drop_table("opportunity_requirements")
    op.drop_table("dedup_decisions")
    op.drop_table("extraction_results")
