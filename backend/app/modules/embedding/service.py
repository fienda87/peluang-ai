import json
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.config import get_settings
from app.shared.logging import get_logger

logger = get_logger("embedding")

LOCAL_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

_st_local_model = None


def _get_local_model():
    global _st_local_model
    if _st_local_model is None:
        from sentence_transformers import SentenceTransformer

        logger.info("loading_local_embedding_model", model=LOCAL_MODEL_NAME)
        _st_local_model = SentenceTransformer(LOCAL_MODEL_NAME)
    return _st_local_model


def embed_texts_local(texts: list[str]) -> list[list[float]]:
    model = _get_local_model()
    vectors = model.encode(texts, normalize_embeddings=True)
    return [v.tolist() for v in vectors]


class EmbeddingService:
    def __init__(self, session: AsyncSession, ai=None) -> None:
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

    async def _backend_embed(self, texts: list[str]) -> list[list[float]]:
        backend = get_settings().embedding_backend
        if backend == "local":
            return embed_texts_local(texts)
        # openrouter (berbayar) — via AI port async
        response = await self.ai.embed(texts)  # type: ignore[union-attr]
        return response.embeddings

    async def _embed_batch(self, opportunity_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[float]]:
        query_result = await self.session.execute(
            text("SELECT id, title, description FROM opportunities WHERE id = ANY(:ids)"),
            {"ids": opportunity_ids},
        )
        rows = query_result.fetchall()

        if not rows:
            return {}

        texts = [f"{row[1]} {row[2] or ''}" for row in rows]
        texts = [t[:2000].strip() for t in texts]

        try:
            embeddings = self._backend_embed(texts)
            pairs = list(zip(rows, embeddings))
        except Exception as e:
            logger.error("embedding_failed", error=str(e), count=len(texts))
            return {}

        result_map = {}
        for (opp_id, _, _), embedding in pairs:
            result_map[opp_id] = embedding

        for opp_id, embedding in result_map.items():
            await self.session.execute(
                text("UPDATE opportunities SET embedding = :emb WHERE id = :id"),
                {"emb": str(embedding), "id": opp_id},
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

        major, skills_json, interests_json, goals_json = row
        skills = json.loads(skills_json) if skills_json else []
        interests = json.loads(interests_json) if interests_json else []
        goals = json.loads(goals_json) if goals_json else []

        profile_text = f"{major} {' '.join(skills)} {' '.join(interests)} {' '.join(goals)}"
        profile_text = profile_text[:2000].strip()

        try:
            embeddings = self._backend_embed([profile_text])
            embedding = embeddings[0] if embeddings else None
        except Exception as e:
            logger.error("user_embedding_failed", user_id=str(user_id), error=str(e))
            return

        if embedding:
            await self.session.execute(
                text("UPDATE user_profiles SET embedding = :emb WHERE user_id = :uid"),
                {"emb": str(embedding), "uid": user_id},
            )
            await self.session.flush()
            logger.info("user_embedding_stored", user_id=str(user_id))
