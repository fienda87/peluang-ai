from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.logging import get_logger

logger = get_logger("analytics")


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_agent_metrics(self) -> list[dict]:
        result = await self.session.execute(
            text(
                "SELECT agent_type, status, count(*) as cnt, "
                "avg(duration_ms) as avg_duration, "
                "sum(llm_call_count) as total_llm_calls, "
                "sum(cost_usd) as total_cost "
                "FROM agent_runs GROUP BY agent_type, status ORDER BY agent_type, status"
            )
        )
        rows = result.fetchall()
        return [
            {
                "agent_type": r[0],
                "status": r[1],
                "count": r[2],
                "avg_duration_ms": round(float(r[3]), 1) if r[3] else 0,
                "total_llm_calls": r[4],
                "total_cost_usd": float(r[5]),
            }
            for r in rows
        ]

    async def get_extraction_success_rate(self) -> float:
        result = await self.session.execute(
            text(
                "SELECT "
                "count(*) FILTER (WHERE status IN ('valid', 'recovered')) as success, "
                "count(*) as total "
                "FROM extraction_results"
            )
        )
        row = result.one_or_none()
        if not row or row[1] == 0:
            return 0.0
        return round(row[0] / row[1], 3)

    async def get_recommendation_metrics(self) -> dict:
        result = await self.session.execute(
            text(
                "SELECT count(DISTINCT run_id) as runs, count(*) as items, "
                "avg(score) as avg_score FROM recommendations"
            )
        )
        row = result.one_or_none()
        return {
            "total_runs": row[0] if row else 0,
            "total_items": row[1] if row else 0,
            "avg_score": round(float(row[2]), 3) if row and row[2] else 0,
        }

    async def get_beta_metrics(self) -> dict:
        users = await self.session.execute(text("SELECT count(*) FROM users"))
        opps = await self.session.execute(
            text("SELECT count(*) FROM opportunities WHERE status = 'active'")
        )
        saves = await self.session.execute(
            text("SELECT count(*) FROM user_events WHERE event_type = 'save'")
        )
        applies = await self.session.execute(
            text("SELECT count(*) FROM user_events WHERE event_type = 'apply'")
        )
        views = await self.session.execute(
            text("SELECT count(*) FROM user_events WHERE event_type IN ('view', 'click')")
        )

        total_users = users.scalar() or 0
        total_opps = opps.scalar() or 0
        total_saves = saves.scalar() or 0
        total_applies = applies.scalar() or 0
        total_views = views.scalar() or 0

        return {
            "total_users": total_users,
            "active_opportunities": total_opps,
            "total_saves": total_saves,
            "total_applies": total_applies,
            "total_views": total_views,
            "save_rate": round(total_saves / total_views, 3) if total_views else 0,
            "apply_rate": round(total_applies / total_views, 3) if total_views else 0,
        }
