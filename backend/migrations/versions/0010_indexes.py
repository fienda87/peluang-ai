"""indexes

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-22
"""
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE INDEX idx_users_telegram_id ON users(telegram_id)")
    op.execute("CREATE INDEX idx_users_email ON users(email)")

    op.execute("CREATE INDEX idx_opportunities_source_id ON opportunities(source_id)")
    op.execute("CREATE INDEX idx_opportunities_status ON opportunities(status)")
    op.execute("CREATE INDEX idx_opportunities_category ON opportunities(category)")
    op.execute("CREATE INDEX idx_opportunities_end_date ON opportunities(end_date)")
    op.execute("CREATE INDEX idx_opportunities_title_trgm ON opportunities USING gin(title gin_trgm_ops)")
    op.execute(
        "CREATE INDEX idx_opportunities_description_fts "
        "ON opportunities USING gin(to_tsvector('simple', coalesce(description, '')))"
    )

    op.execute("CREATE INDEX idx_raw_documents_source_id ON raw_documents(source_id)")
    op.execute("CREATE INDEX idx_raw_documents_opportunity_id ON raw_documents(opportunity_id)")
    op.execute("CREATE INDEX idx_raw_documents_ingestion_run_id ON raw_documents(ingestion_run_id)")

    op.execute("CREATE INDEX idx_ingestion_runs_source ON ingestion_runs(source_id, started_at DESC)")
    op.execute("CREATE INDEX idx_ingestion_runs_status ON ingestion_runs(status)")

    op.execute("CREATE INDEX idx_extraction_results_raw_doc ON extraction_results(raw_document_id)")
    op.execute("CREATE INDEX idx_extraction_results_status ON extraction_results(status)")
    op.execute("CREATE INDEX idx_extraction_results_opportunity ON extraction_results(opportunity_id)")

    op.execute("CREATE INDEX idx_dedup_duplicate_of ON dedup_decisions(duplicate_of_id)")

    op.execute("CREATE INDEX idx_requirements_opportunity ON opportunity_requirements(opportunity_id)")

    op.execute("CREATE INDEX idx_eligibility_user_status ON opportunity_eligibility(user_id, status)")
    op.execute("CREATE INDEX idx_eligibility_opportunity ON opportunity_eligibility(opportunity_id)")

    op.execute("CREATE INDEX idx_recommendation_runs_user ON recommendation_runs(user_id, created_at DESC)")
    op.execute("CREATE INDEX idx_recommendations_user_recommended ON recommendations(user_id, recommended_at DESC)")
    op.execute("CREATE INDEX idx_recommendations_run_id ON recommendations(run_id)")
    op.execute("CREATE INDEX idx_recommendations_opportunity ON recommendations(opportunity_id)")

    op.execute("CREATE INDEX idx_user_events_user_created ON user_events(user_id, created_at DESC)")
    op.execute("CREATE INDEX idx_user_events_type ON user_events(event_type)")
    op.execute("CREATE INDEX idx_user_events_opportunity ON user_events(opportunity_id)")

    op.execute("CREATE INDEX idx_behavior_insights_user ON behavior_insights(user_id, created_at DESC)")
    op.execute("CREATE INDEX idx_behavior_insights_status ON behavior_insights(status)")

    op.execute("CREATE INDEX idx_notifications_dispatch ON notifications(status, scheduled_at)")
    op.execute("CREATE INDEX idx_notifications_user ON notifications(user_id, created_at DESC)")

    op.execute("CREATE INDEX idx_agent_runs_lookup ON agent_runs(agent_type, status, started_at DESC)")
    op.execute("CREATE INDEX idx_agent_runs_source ON agent_runs(source_id)")
    op.execute("CREATE INDEX idx_agent_runs_user ON agent_runs(user_id)")
    op.execute("CREATE INDEX idx_agent_runs_failure ON agent_runs(failure_code) WHERE failure_code IS NOT NULL")

    op.execute("CREATE INDEX idx_agent_run_events_run ON agent_run_events(agent_run_id, step)")


def downgrade() -> None:
    indexes = [
        ("users", "idx_users_telegram_id"),
        ("users", "idx_users_email"),
        ("opportunities", "idx_opportunities_source_id"),
        ("opportunities", "idx_opportunities_status"),
        ("opportunities", "idx_opportunities_category"),
        ("opportunities", "idx_opportunities_end_date"),
        ("opportunities", "idx_opportunities_title_trgm"),
        ("opportunities", "idx_opportunities_description_fts"),
        ("raw_documents", "idx_raw_documents_source_id"),
        ("raw_documents", "idx_raw_documents_opportunity_id"),
        ("raw_documents", "idx_raw_documents_ingestion_run_id"),
        ("ingestion_runs", "idx_ingestion_runs_source"),
        ("ingestion_runs", "idx_ingestion_runs_status"),
        ("extraction_results", "idx_extraction_results_raw_doc"),
        ("extraction_results", "idx_extraction_results_status"),
        ("extraction_results", "idx_extraction_results_opportunity"),
        ("dedup_decisions", "idx_dedup_duplicate_of"),
        ("opportunity_requirements", "idx_requirements_opportunity"),
        ("opportunity_eligibility", "idx_eligibility_user_status"),
        ("opportunity_eligibility", "idx_eligibility_opportunity"),
        ("recommendation_runs", "idx_recommendation_runs_user"),
        ("recommendations", "idx_recommendations_user_recommended"),
        ("recommendations", "idx_recommendations_run_id"),
        ("recommendations", "idx_recommendations_opportunity"),
        ("user_events", "idx_user_events_user_created"),
        ("user_events", "idx_user_events_type"),
        ("user_events", "idx_user_events_opportunity"),
        ("behavior_insights", "idx_behavior_insights_user"),
        ("behavior_insights", "idx_behavior_insights_status"),
        ("notifications", "idx_notifications_dispatch"),
        ("notifications", "idx_notifications_user"),
        ("agent_runs", "idx_agent_runs_lookup"),
        ("agent_runs", "idx_agent_runs_source"),
        ("agent_runs", "idx_agent_runs_user"),
        ("agent_runs", "idx_agent_runs_failure"),
        ("agent_run_events", "idx_agent_run_events_run"),
    ]
    for table, name in indexes:
        op.execute(f"DROP INDEX IF EXISTS {name}")
