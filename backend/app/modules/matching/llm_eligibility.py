import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai import get_ai
from app.shared.logging import get_logger

logger = get_logger("matching.llm")


class LLMElibilityService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def evaluate_semantic(
        self,
        user_id: uuid.UUID,
        opportunity_id: uuid.UUID,
        requirement_text: str,
    ) -> dict:
        user_result = await self.session.execute(
            text("SELECT major, skills, interests FROM user_profiles WHERE user_id = :uid"),
            {"uid": user_id},
        )
        row = user_result.one_or_none()
        if not row:
            return {"status": "UNKNOWN", "confidence": 0.3}

        import json

        major, skills_json, interests_json = row
        skills = json.loads(skills_json) if skills_json else []
        interests = json.loads(interests_json) if interests_json else []

        prompt = (
            f"User profile: major={major}, skills={skills}, interests={interests}\n"
            f"Requirement: {requirement_text}\n"
            "Does this user meet the requirement? "
            'Return JSON: {"status": "ELIGIBLE|INELIGIBLE|UNKNOWN", "confidence": 0.0-1.0, "reason": "..."}'
        )

        try:
            ai = get_ai()
            response = await ai.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=200,
            )
            data = json.loads(response.content)
            return {
                "status": data.get("status", "UNKNOWN"),
                "confidence": float(data.get("confidence", 0.5)),
                "reason": data.get("reason", ""),
            }
        except Exception as e:
            logger.error("llm_eligibility_failed", error=str(e))
            return {"status": "UNKNOWN", "confidence": 0.3}
