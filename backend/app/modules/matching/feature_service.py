import uuid
from datetime import date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.logging import get_logger

logger = get_logger("matching.features")


class MatchFeatureService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def build_match_features(
        self,
        user_id: uuid.UUID,
        opportunity_id: uuid.UUID,
    ) -> dict:
        opp_result = await self.session.execute(
            text(
                "SELECT category, location, end_date, embedding FROM opportunities WHERE id = :oid"
            ),
            {"oid": opportunity_id},
        )
        opp_row = opp_result.one_or_none()

        user_result = await self.session.execute(
            text("SELECT interests, location, embedding FROM user_profiles WHERE user_id = :uid"),
            {"uid": user_id},
        )
        user_row = user_result.one_or_none()

        if not opp_row or not user_row:
            return {"category_fit": 0.0, "location_fit": 0.0, "urgency": 0.0, "semantic": 0.0}

        import json

        opp_category, opp_location, opp_end_date, opp_emb = opp_row
        user_interests_json, user_location, user_emb = user_row
        user_interests = json.loads(user_interests_json) if user_interests_json else []

        category_fit = 1.0 if opp_category in user_interests else 0.3

        location_fit = 0.0
        if user_location and opp_location:
            if user_location.lower() in opp_location.lower() or opp_location.lower() in user_location.lower():
                location_fit = 1.0
            elif "online" in opp_location.lower() or "seluruh" in opp_location.lower():
                location_fit = 0.8

        urgency = 0.0
        if opp_end_date:
            days_left = (opp_end_date - date.today()).days
            if 0 <= days_left <= 7:
                urgency = 1.0
            elif days_left <= 14:
                urgency = 0.7
            elif days_left <= 30:
                urgency = 0.4

        semantic = 0.0
        if opp_emb and user_emb:
            semantic = self._cosine_similarity(opp_emb, user_emb)

        return {
            "category_fit": category_fit,
            "location_fit": location_fit,
            "urgency": urgency,
            "semantic": semantic,
        }

    def _cosine_similarity(self, a, b) -> float:
        try:
            if isinstance(a, str):
                a = [float(x) for x in a.strip("[]").split(",")]
            if isinstance(b, str):
                b = [float(x) for x in b.strip("[]").split(",")]
            dot = sum(x * y for x, y in zip(a, b))
            norm_a = sum(x * x for x in a) ** 0.5
            norm_b = sum(x * x for x in b) ** 0.5
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return dot / (norm_a * norm_b)
        except Exception:
            return 0.0

    async def score_match(self, user_id: uuid.UUID, opportunity_id: uuid.UUID) -> float:
        features = await self.build_match_features(user_id, opportunity_id)

        weights = {"category_fit": 0.35, "location_fit": 0.15, "urgency": 0.2, "semantic": 0.3}

        score = sum(features.get(k, 0.0) * w for k, w in weights.items())
        return round(min(score, 1.0), 4)
