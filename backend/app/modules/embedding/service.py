import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai import AIPort
from app.shared.logging import get_logger

logger = get_logger("embedding")


class EmbeddingService:
    def __init__(self, session: AsyncSession, ai: AIPort) -> None:
        self.session = session
        self.ai = ai

    async def embed_opportunities(
        self,
        opportunity_ids: list[uuid.UUID],
        batch_size: int = 100,
    ) -> dict[uuid.UUID, list[float]]:
        results = {}

        for i in range(0, len(opportunity_ids), batch_size):
            batch_ids = opportunity_ids[i : i + batch_size]
            batch_results = await self._embed_batch(batch_ids)
            results.update(batch_results)

        return results

    async def _embed_batch(self, opportunity_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[float]]:
        query_result = await self.session.execute(
            text(
                "SELECT id, title, description FROM opportunities WHERE id = ANY(:ids)"
            ),
            {"ids": opportunity_ids},
        )
        rows = query_result.fetchall()

        if not rows:
            return {}

        texts = [f"{row[1]} {row[2] or ''}" for row in rows]
        texts = [t[:2000].strip() for t in texts]

        try:
            embedding_response = await self.ai.embed(texts)
        except Exception as e:
            logger.error("embedding_failed", error=str(e), count=len(texts))
            return {}

        result_map = {}
        for (opp_id, _, _), embedding in zip(rows, embedding_response.embeddings):
            result_map[opp_id] = embedding

        for opp_id, embedding in result_map.items():
            embedding_str = str(embedding).replace("[", "[").replace("]", "]")
            await self.session.execute(
                text("UPDATE opportunities SET embedding = :emb WHERE id = :id"),
                {"emb": embedding_str, "id": opp_id},
            )

        await self.session.flush()
        logger.info("embeddings_stored", count=len(result_map))
        return result_map

    async def embed_user_profile(self, user_id: uuid.UUID) -> None:
        result = await self.session.execute(
            text(
                "SELECT major, skills, interests, goals FROM user_profiles WHERE user_id = :uid"
            ),
            {"uid": user_id},
        )
        row = result.one_or_none()
        if not row:
            return

        import json

        major, skills_json, interests_json, goals_json = row
        skills = json.loads(skills_json) if skills_json else []
        interests = json.loads(interests_json) if interests_json else []
        goals = json.loads(goals_json) if goals_json else []

        profile_text = f"{major} {' '.join(skills)} {' '.join(interests)} {' '.join(goals)}"
        profile_text = profile_text[:2000].strip()

        try:
            embedding_response = await self.ai.embed([profile_text])
            embedding = embedding_response.embeddings[0] if embedding_response.embeddings else None
        except Exception as e:
            logger.error("user_embedding_failed", user_id=str(user_id), error=str(e))
            return

        if embedding:
            embedding_str = str(embedding)
            await self.session.execute(
                text("UPDATE user_profiles SET embedding = :emb WHERE user_id = :uid"),
                {"emb": embedding_str, "uid": user_id},
            )
            await self.session.flush()
            logger.info("user_embedding_stored", user_id=str(user_id))
