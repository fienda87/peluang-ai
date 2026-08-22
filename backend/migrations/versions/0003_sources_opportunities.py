"""sources and opportunities

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-22
"""
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(100), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("access_method", sa.String(100), nullable=False, server_default="http"),
        sa.Column("crawl_frequency", sa.String(50), nullable=False, server_default="daily"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("health_status", sa.String(50), nullable=False, server_default="healthy"),
        sa.Column("last_crawled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consecutive_errors", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("meta", sa.dialects.postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("source_type IN ('web','api','rss','community','manual')", name="ck_sources_type"),
        sa.CheckConstraint("access_method IN ('http','crawl4ai','playwright','rss','api','manual')", name="ck_sources_access"),
        sa.CheckConstraint("health_status IN ('healthy','degraded','paused','blocked')", name="ck_sources_health"),
    )
    op.execute("CREATE TRIGGER trg_sources_updated_at BEFORE UPDATE ON sources FOR EACH ROW EXECUTE FUNCTION set_updated_at()")

    op.create_table(
        "opportunities",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("source_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("slug", sa.String(255), unique=True, nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("sub_category", sa.String(100), nullable=True),
        sa.Column("organizer", sa.String(255), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("prize", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("meta", sa.dialects.postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "category IN ('beasiswa','lomba','magang','fellowship','konferensi','volunteer','pelatihan','riset','kompetisi','lainnya')",
            name="ck_opportunities_category",
        ),
        sa.CheckConstraint("status IN ('draft','active','expired','archived')", name="ck_opportunities_status"),
    )
    op.execute("ALTER TABLE opportunities ADD COLUMN embedding vector(1536)")
    op.execute("CREATE TRIGGER trg_opportunities_updated_at BEFORE UPDATE ON opportunities FOR EACH ROW EXECUTE FUNCTION set_updated_at()")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_opportunities_updated_at ON opportunities")
    op.execute("DROP TRIGGER IF EXISTS trg_sources_updated_at ON sources")
    op.drop_table("opportunities")
    op.drop_table("sources")
