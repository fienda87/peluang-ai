"""user events, behavior insights, preferences, notifications

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-22
"""
import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_events",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("opportunity_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("recommendation_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("recommendations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("metadata", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "event_type IN ('view','save','click','apply','expire','win','remove','feedback','ignore','reject')",
            name="ck_user_events_type",
        ),
    )

    op.create_table(
        "behavior_insights",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_run_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("insight_type", sa.String(50), nullable=False),
        sa.Column("preference_delta", sa.dialects.postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("confidence", sa.Numeric(5, 2), nullable=False),
        sa.Column("evidence_event_ids", sa.dialects.postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(30), nullable=False, server_default="proposed"),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1.00", name="ck_behavior_insights_confidence"),
        sa.CheckConstraint("status IN ('proposed','applied','rejected','held')", name="ck_behavior_insights_status"),
    )

    op.create_table(
        "user_preferences",
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("category_weights", sa.dialects.postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("preferred_locations", sa.dialects.postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("excluded_categories", sa.dialects.postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("notification_settings", sa.dialects.postgresql.JSONB(), nullable=False, server_default='{"daily_digest": true, "deadline_reminders": true}'),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("updated_by_agent_run_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.execute("CREATE TRIGGER trg_user_preferences_updated_at BEFORE UPDATE ON user_preferences FOR EACH ROW EXECUTE FUNCTION set_updated_at()")

    op.create_table(
        "notifications",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("opportunity_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("notification_type", sa.String(50), nullable=False),
        sa.Column("channel", sa.String(30), nullable=False, server_default="telegram"),
        sa.Column("status", sa.String(30), nullable=False, server_default="scheduled"),
        sa.Column("idempotency_key", sa.String(255), unique=True, nullable=False),
        sa.Column("payload", sa.dialects.postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "notification_type IN ('daily_digest','deadline_d3','deadline_d1','deadline_urgent','new_recommendation')",
            name="ck_notifications_type",
        ),
        sa.CheckConstraint("channel IN ('telegram','email')", name="ck_notifications_channel"),
        sa.CheckConstraint("status IN ('scheduled','sent','failed','cancelled')", name="ck_notifications_status"),
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_user_preferences_updated_at ON user_preferences")
    op.drop_table("notifications")
    op.drop_table("user_preferences")
    op.drop_table("behavior_insights")
    op.drop_table("user_events")
