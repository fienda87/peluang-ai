import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.logging import get_logger

logger = get_logger("ingestion.health")

DEGRADED_THRESHOLD = 3
PAUSED_THRESHOLD = 5


class SourceHealthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_success(self, source_id: uuid.UUID) -> None:
        await self.session.execute(
            text(
                "UPDATE sources SET consecutive_errors = 0, health_status = 'healthy', "
                "last_crawled_at = now() WHERE id = :id"
            ),
            {"id": source_id},
        )
        await self.session.commit()

    async def record_error(self, source_id: uuid.UUID) -> str:
        result = await self.session.execute(
            text(
                "UPDATE sources SET consecutive_errors = consecutive_errors + 1 "
                "WHERE id = :id RETURNING consecutive_errors"
            ),
            {"id": source_id},
        )
        errors = result.scalar_one()

        if errors >= PAUSED_THRESHOLD:
            status = "paused"
        elif errors >= DEGRADED_THRESHOLD:
            status = "degraded"
        else:
            status = "healthy"

        await self.session.execute(
            text("UPDATE sources SET health_status = :status WHERE id = :id"),
            {"status": status, "id": source_id},
        )
        await self.session.commit()
        logger.info("source_health_updated", source_id=str(source_id), status=status, errors=errors)
        return status

    async def get_health(self, source_id: uuid.UUID) -> dict | None:
        result = await self.session.execute(
            text(
                "SELECT id, name, health_status, consecutive_errors, last_crawled_at "
                "FROM sources WHERE id = :id"
            ),
            {"id": source_id},
        )
        row = result.one_or_none()
        if not row:
            return None
        return {
            "id": str(row[0]),
            "name": row[1],
            "health_status": row[2],
            "consecutive_errors": row[3],
            "last_crawled_at": str(row[4]) if row[4] else None,
        }
