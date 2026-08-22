import json
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.matching.candidate_service import CandidateService
from app.shared.logging import get_logger

logger = get_logger("recommendation.service")


class RecommendationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.candidates = CandidateService(session)

    async def generate(
        self,
        user_id: uuid.UUID,
        trigger: str = "cron",
        top_n: int = 20,
    ) -> dict:
        run_id = uuid.uuid4()
        await self.session.execute(
            text(
                "INSERT INTO recommendation_runs (id, user_id, trigger) VALUES (:id, :uid, :trigger)"
            ),
            {"id": run_id, "uid": user_id, "trigger": trigger},
        )

        candidates = await self.candidates.list_candidates(user_id, limit=100)
        top = candidates[:top_n]

        for rank, c in enumerate(top, 1):
            opp_id = uuid.UUID(c["opportunity_id"])
            explanation = {
                "reason": "Kecocokan kategori dan urgensi tenggat waktu",
                "score": c["score"],
                "eligibility": c["eligibility"],
            }
            await self.session.execute(
                text(
                    "INSERT INTO recommendations "
                    "(id, run_id, user_id, opportunity_id, score, rank_position, reasoning, context_snapshot) "
                    "VALUES (:id, :run_id, :uid, :oid, :score, :rank, :reasoning, :ctx)"
                ),
                {
                    "id": uuid.uuid4(),
                    "run_id": run_id,
                    "uid": user_id,
                    "oid": opp_id,
                    "score": c["score"],
                    "rank": rank,
                    "reasoning": json.dumps(explanation),
                    "ctx": json.dumps({"trigger": trigger}),
                },
            )

        await self.session.execute(
            text(
                "UPDATE recommendation_runs SET candidate_count = :cc, recommended_count = :rc WHERE id = :id"
            ),
            {"cc": len(candidates), "rc": len(top), "id": run_id},
        )
        await self.session.commit()

        logger.info(
            "recommendations_generated",
            user_id=str(user_id),
            candidates=len(candidates),
            recommended=len(top),
        )
        return {"run_id": str(run_id), "count": len(top)}

    async def get_feed(self, user_id: uuid.UUID, limit: int = 20) -> list[dict]:
        result = await self.session.execute(
            text(
                "SELECT r.opportunity_id, r.score, r.rank_position, r.reasoning, o.title, o.slug, "
                "o.category, o.organizer, o.end_date "
                "FROM recommendations r JOIN opportunities o ON o.id = r.opportunity_id "
                "WHERE r.user_id = :uid "
                "ORDER BY r.recommended_at DESC, r.rank_position ASC LIMIT :limit"
            ),
            {"uid": user_id, "limit": limit},
        )
        rows = result.fetchall()
        return [
            {
                "opportunity_id": str(r[0]),
                "score": float(r[1]),
                "rank": r[2],
                "reasoning": json.loads(r[3]) if r[3] else {},
                "title": r[4],
                "slug": r[5],
                "category": r[6],
                "organizer": r[7],
                "end_date": str(r[8]) if r[8] else None,
            }
            for r in rows
        ]
