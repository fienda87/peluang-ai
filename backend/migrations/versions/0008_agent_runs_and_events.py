"""agent runs and agent run events

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-22
"""
import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_runs",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("agent_type", sa.String(30), nullable=False),
        sa.Column("agent_version", sa.String(50), nullable=False, server_default="1.0.0"),
        sa.Column("graph_version", sa.String(50), nullable=False, server_default="1.0.0"),
        sa.Column("model_key", sa.String(100), nullable=True),
        sa.Column("trigger", sa.String(50), nullable=False, server_default="manual"),
        sa.Column("status", sa.String(30), nullable=False, server_default="running"),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("opportunity_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("step_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("llm_call_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tokens_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=False, server_default="0"),
        sa.Column("failure_code", sa.String(50), nullable=True),
        sa.Column("input_summary", sa.dialects.postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("output_summary", sa.dialects.postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "agent_type IN ('discovery','extraction','recovery','recommendation','feedback')",
            name="ck_agent_runs_type",
        ),
        sa.CheckConstraint(
            "status IN ('running','success','failed','timeout','cancelled','degraded','budget_exhausted','paused')",
            name="ck_agent_runs_status",
        ),
        sa.CheckConstraint(
            "failure_code IS NULL OR failure_code IN ("
            "'PROVIDER_TIMEOUT','PROVIDER_RATE_LIMIT','PROVIDER_ERROR',"
            "'SCHEMA_VALIDATION_FAILED','BUDGET_EXHAUSTED','SOURCE_BLOCKED',"
            "'OCR_LOW_CONFIDENCE','NO_CONTENT_FOUND','DUPLICATE_DETECTED',"
            "'PARSE_FAILED','NETWORK_ERROR','UNKNOWN')",
            name="ck_agent_runs_failure_code",
        ),
    )

    op.create_table(
        "agent_run_events",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("agent_run_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("payload", sa.dialects.postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "event_type IN ('tool_call','llm_call','state_change','error','info')",
            name="ck_agent_run_events_type",
        ),
    )


def downgrade() -> None:
    op.drop_table("agent_run_events")
    op.drop_table("agent_runs")
