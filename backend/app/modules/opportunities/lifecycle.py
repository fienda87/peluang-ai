from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.logging import get_logger

logger = get_logger("opportunities.lifecycle")


class LifecycleService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def expire_past_deadlines(self) -> int:
        result = await self.session.execute(
            text(
                "UPDATE opportunities SET status = 'expired' "
                "WHERE status = 'active' AND end_date IS NOT NULL AND end_date < CURRENT_DATE "
                "RETURNING id"
            )
        )
        expired = result.fetchall()
        await self.session.commit()
        logger.info("opportunities_expired", count=len(expired))
        return len(expired)
