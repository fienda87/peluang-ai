"""embedding dims 1536 -> 384 (local MiniLM per Tech Spec §32 embeddings local preferred)

Revision ID: 0011
Revises: 0010
Create Date: 2026-08-23
"""
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE opportunities ALTER COLUMN embedding TYPE vector(384) USING NULL")
    op.execute("ALTER TABLE user_profiles ALTER COLUMN embedding TYPE vector(384) USING NULL")


def downgrade() -> None:
    op.execute("ALTER TABLE opportunities ALTER COLUMN embedding TYPE vector(1536) USING NULL")
    op.execute("ALTER TABLE user_profiles ALTER COLUMN embedding TYPE vector(1536) USING NULL")
