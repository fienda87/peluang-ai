"""circular foreign keys

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-22
"""
import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agent_runs", sa.Column("raw_document_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_agent_runs_raw_document", "agent_runs", "raw_documents", ["raw_document_id"], ["id"], ondelete="SET NULL")

    op.add_column("ingestion_runs", sa.Column("agent_run_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_ingestion_runs_agent_run", "ingestion_runs", "agent_runs", ["agent_run_id"], ["id"], ondelete="SET NULL")

    op.add_column("extraction_results", sa.Column("agent_run_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_extraction_agent_run", "extraction_results", "agent_runs", ["agent_run_id"], ["id"], ondelete="SET NULL")

    op.create_foreign_key("fk_eligibility_agent_run", "opportunity_eligibility", "agent_runs", ["checked_by_agent_run_id"], ["id"], ondelete="SET NULL")

    op.add_column("recommendation_runs", sa.Column("agent_run_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_recommendation_runs_agent_run", "recommendation_runs", "agent_runs", ["agent_run_id"], ["id"], ondelete="SET NULL")

    op.create_foreign_key("fk_insight_agent_run", "behavior_insights", "agent_runs", ["agent_run_id"], ["id"], ondelete="SET NULL")

    op.create_foreign_key("fk_preferences_agent_run", "user_preferences", "agent_runs", ["updated_by_agent_run_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    op.drop_constraint("fk_preferences_agent_run", "user_preferences", type_="foreignkey")
    op.drop_constraint("fk_insight_agent_run", "behavior_insights", type_="foreignkey")
    op.drop_constraint("fk_recommendation_runs_agent_run", "recommendation_runs", type_="foreignkey")
    op.drop_constraint("fk_eligibility_agent_run", "opportunity_eligibility", type_="foreignkey")
    op.drop_constraint("fk_extraction_agent_run", "extraction_results", type_="foreignkey")
    op.drop_column("extraction_results", "agent_run_id")
    op.drop_constraint("fk_ingestion_runs_agent_run", "ingestion_runs", type_="foreignkey")
    op.drop_column("ingestion_runs", "agent_run_id")
    op.drop_constraint("fk_agent_runs_raw_document", "agent_runs", type_="foreignkey")
    op.drop_column("agent_runs", "raw_document_id")
