"""eligibility and recommendations

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-22
"""
import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "opportunity_eligibility",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("opportunity_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 2), nullable=False),
        sa.Column("matched_requirements", sa.dialects.postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("missing_requirements", sa.dialects.postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("checked_by_agent_run_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('ELIGIBLE','INELIGIBLE','UNKNOWN')", name="ck_eligibility_status"),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1.00", name="ck_eligibility_confidence"),
        sa.UniqueConstraint("user_id", "opportunity_id", name="uq_user_opportunity_eligibility"),
    )

    op.create_table(
        "recommendation_runs",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("candidate_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("recommended_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("trigger", sa.String(50), nullable=False, server_default="cron"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("trigger IN ('cron','on_demand','behavior_update','new_opportunity')", name="ck_recommendation_runs_trigger"),
    )

    op.create_table(
        "recommendations",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("run_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("recommendation_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("opportunity_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("score", sa.Numeric(5, 4), nullable=False),
        sa.Column("rank_position", sa.Integer(), nullable=False),
        sa.Column("reasoning", sa.dialects.postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("context_snapshot", sa.dialects.postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("recommended_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("recommendations")
    op.drop_table("recommendation_runs")
    op.drop_table("opportunity_eligibility")
