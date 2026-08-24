import uuid

from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.matching.eligibility_service import EligibilityService
from app.modules.matching.feature_service import MatchFeatureService
from app.shared.logging import get_logger

logger = get_logger("matching.candidates")


class CandidateService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.eligibility = EligibilityService(session)
        self.features = MatchFeatureService(session)

    async def list_candidates(
        self,
        user_id: uuid.UUID,
        limit: int = 100,
    ) -> list[dict]:
        # §10 Runtime Doc: pgvector retrieval dulu, sisanya fallback by deadline
        emb_result = await self.session.execute(
            text("SELECT embedding FROM user_profiles WHERE user_id = :uid"),
            {"uid": user_id},
        )
        profile_emb = emb_result.scalar()

        if profile_emb is not None:
            result = await self.session.execute(
                text(
                    "SELECT id FROM opportunities WHERE status = 'active' "
                    "AND (end_date IS NULL OR end_date >= CURRENT_DATE) "
                    "AND embedding IS NOT NULL "
                    "ORDER BY embedding <=> :pemb LIMIT :limit"
                ),
                {"pemb": str(profile_emb), "limit": limit},
            )
            opp_ids = [row[0] for row in result.fetchall()]

        if profile_emb is None or len(opp_ids) < limit:
            exclude = tuple(opp_ids) or (uuid.UUID(int=0),)
            result = await self.session.execute(
                text(
                    "SELECT id FROM opportunities WHERE status = 'active' "
                    "AND (end_date IS NULL OR end_date >= CURRENT_DATE) "
                    "AND id NOT IN :exclude "
                    "ORDER BY end_date ASC NULLS LAST LIMIT :limit"
                ).bindparams(bindparam("exclude", expanding=True)),
                {"exclude": list(exclude), "limit": limit},
            )
            opp_ids += [row[0] for row in result.fetchall()]

        candidates = []
        for opp_id in opp_ids:
            eligibility = await self.eligibility.evaluate_eligibility(user_id, opp_id)

            if eligibility["status"] == "INELIGIBLE":
                continue

            score = await self.features.score_match(user_id, opp_id)

            if eligibility["status"] == "UNKNOWN":
                score *= 0.7

            candidates.append(
                {
                    "opportunity_id": str(opp_id),
                    "eligibility": eligibility["status"],
                    "score": score,
                }
            )

        candidates.sort(key=lambda c: c["score"], reverse=True)
        logger.info("candidates_listed", user_id=str(user_id), count=len(candidates))
        return candidates
