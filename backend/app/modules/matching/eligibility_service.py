import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.logging import get_logger

logger = get_logger("matching")


class EligibilityService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def evaluate_eligibility(
        self,
        user_id: uuid.UUID,
        opportunity_id: uuid.UUID,
    ) -> dict:
        user_result = await self.session.execute(
            text("SELECT cgpa, major, graduation_year FROM user_profiles WHERE user_id = :uid"),
            {"uid": user_id},
        )
        user_row = user_result.one_or_none()

        opp_result = await self.session.execute(
            text("SELECT id FROM opportunity_requirements WHERE opportunity_id = :oid"),
            {"oid": opportunity_id},
        )
        reqs = opp_result.fetchall()

        if not user_row or not reqs:
            status = "UNKNOWN"
            confidence = 0.5
            matched = []
            missing = []
        else:
            user_cgpa, user_major, user_grad_year = user_row
            status = "ELIGIBLE"
            confidence = 0.8
            matched = []
            missing = []

            for req in reqs:
                if "gpa" in req[0].lower() and user_cgpa:
                    matched.append("gpa_requirement")
                elif "major" in req[0].lower() and user_major:
                    matched.append("major_requirement")

            if user_cgpa is None:
                missing.append("gpa_data")
            if user_major is None:
                missing.append("major_data")

        import json
        await self.session.execute(
            text(
                "INSERT INTO opportunity_eligibility "
                "(opportunity_id, user_id, status, confidence, matched_requirements, missing_requirements, checked_at) "
                "VALUES (:opp_id, :user_id, :status, :conf, :matched, :missing, now()) "
                "ON CONFLICT (user_id, opportunity_id) DO UPDATE SET status = :status, confidence = :conf"
            ),
            {
                "opp_id": opportunity_id,
                "user_id": user_id,
                "status": status,
                "conf": confidence,
                "matched": json.dumps(matched),
                "missing": json.dumps(missing),
            },
        )
        await self.session.flush()

        logger.info(
            "eligibility_evaluated",
            user_id=str(user_id),
            opp_id=str(opportunity_id),
            status=status,
        )

        return {
            "opportunity_id": str(opportunity_id),
            "user_id": str(user_id),
            "status": status,
            "confidence": confidence,
            "matched_requirements": matched,
            "missing_requirements": missing,
        }
