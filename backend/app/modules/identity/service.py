import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.logging import get_logger

logger = get_logger("identity")


class IdentityService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_profile(self, user_id: uuid.UUID) -> dict:
        result = await self.session.execute(
            text(
                "SELECT user_id, education_level, major, university, graduation_year, cgpa, "
                "skills, experience, interests, goals, location FROM user_profiles WHERE user_id = :uid"
            ),
            {"uid": user_id},
        )
        row = result.one_or_none()
        if not row:
            return None

        import json

        def _list(v):
            if isinstance(v, str):
                return json.loads(v)
            return v or []

        return {
            "user_id": str(row[0]),
            "education_level": row[1],
            "major": row[2],
            "university": row[3],
            "graduation_year": row[4],
            "cgpa": float(row[5]) if row[5] else None,
            "skills": _list(row[6]),
            "experience": _list(row[7]),
            "interests": _list(row[8]),
            "goals": _list(row[9]),
            "location": row[10],
        }

    async def update_profile(self, user_id: uuid.UUID, **kwargs) -> dict:
        import json
        fields = []
        params = {"uid": user_id}
        for k, v in kwargs.items():
            if k in ("skills", "experience", "interests", "goals"):
                v = json.dumps(v) if isinstance(v, (list, dict)) else v
            fields.append(f"{k} = :{k}")
            params[k] = v

        if fields:
            query = f"UPDATE user_profiles SET {', '.join(fields)} WHERE user_id = :uid"
            await self.session.execute(text(query), params)
            await self.session.flush()

        logger.info("profile_updated", user_id=str(user_id))
        return await self.get_profile(user_id)

    async def get_preferences(self, user_id: uuid.UUID) -> dict:
        result = await self.session.execute(
            text(
                "SELECT category_weights, preferred_locations, excluded_categories, notification_settings "
                "FROM user_preferences WHERE user_id = :uid"
            ),
            {"uid": user_id},
        )
        row = result.one_or_none()
        if not row:
            return None

        import json
        return {
            "category_weights": json.loads(row[0]) if row[0] else {},
            "preferred_locations": json.loads(row[1]) if row[1] else [],
            "excluded_categories": json.loads(row[2]) if row[2] else [],
            "notification_settings": json.loads(row[3]) if row[3] else {},
        }
