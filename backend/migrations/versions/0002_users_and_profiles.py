"""users and profiles

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-22
"""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), unique=True, nullable=True),
        sa.Column("email", sa.String(255), unique=True, nullable=True),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("first_name", sa.String(255), nullable=True),
        sa.Column("last_name", sa.String(255), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("auth_provider", sa.String(50), nullable=False, server_default="local"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("auth_provider IN ('local','telegram','google')", name="ck_users_auth_provider"),
    )
    op.execute("CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION set_updated_at()")

    op.create_table(
        "user_profiles",
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("education_level", sa.String(100), nullable=True),
        sa.Column("major", sa.String(255), nullable=True),
        sa.Column("university", sa.String(255), nullable=True),
        sa.Column("graduation_year", sa.Integer(), nullable=True),
        sa.Column("cgpa", sa.Numeric(3, 2), nullable=True),
        sa.Column("skills", sa.dialects.postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("experience", sa.dialects.postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("interests", sa.dialects.postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("goals", sa.dialects.postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("cgpa >= 0 AND cgpa <= 4.00", name="ck_user_profiles_cgpa"),
    )
    op.execute("ALTER TABLE user_profiles ADD COLUMN embedding vector(1536)")
    op.execute("CREATE TRIGGER trg_user_profiles_updated_at BEFORE UPDATE ON user_profiles FOR EACH ROW EXECUTE FUNCTION set_updated_at()")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_user_profiles_updated_at ON user_profiles")
    op.execute("DROP TRIGGER IF EXISTS trg_users_updated_at ON users")
    op.drop_table("user_profiles")
    op.drop_table("users")
