import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://peluang:peluang_dev@localhost:5432/peluang")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET", "test-secret")
