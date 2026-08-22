from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.logging import get_logger

logger = get_logger("retention")


class RetentionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def purge_old_data(self) -> dict:
        results = {}

        r = await self.session.execute(
            text("DELETE FROM agent_run_events WHERE created_at < now() - interval '30 days' RETURNING id")
        )
        results["agent_run_events"] = len(r.fetchall())

        r = await self.session.execute(
            text("DELETE FROM user_events WHERE created_at < now() - interval '365 days' RETURNING id")
        )
        results["user_events"] = len(r.fetchall())

        r = await self.session.execute(
            text("DELETE FROM recommendations WHERE recommended_at < now() - interval '90 days' RETURNING id")
        )
        results["recommendations"] = len(r.fetchall())

        r = await self.session.execute(
            text("DELETE FROM recommendation_runs WHERE created_at < now() - interval '90 days' RETURNING id")
        )
        results["recommendation_runs"] = len(r.fetchall())

        r = await self.session.execute(
            text("DELETE FROM notifications WHERE status IN ('sent', 'cancelled') AND created_at < now() - interval '30 days' RETURNING id")
        )
        results["notifications"] = len(r.fetchall())

        await self.session.commit()
        logger.info("retention_purge_done", **results)
        return results
