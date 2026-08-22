import json
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.behavior.service import BehaviorService
from app.shared.logging import get_logger

logger = get_logger("feedback.service")


class FeedbackService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.behavior = BehaviorService(session)

    async def run_feedback_cycle(self, user_id: uuid.UUID) -> dict:
        profile = await self.behavior.get_behavior_profile(user_id)

        if profile["total_events"] < 5:
            logger.info("feedback_skipped_insufficient", user_id=str(user_id))
            return {"decision": "no_update", "reason": "insufficient_events"}

        affinity = profile.get("category_affinity", {})
        if not affinity:
            return {"decision": "no_update", "reason": "no_affinity_signal"}

        confidence = 0.8 if len(affinity) >= 2 else 0.5
        decision = "apply" if confidence >= 0.7 else "hold"

        insight_id = uuid.uuid4()
        await self.session.execute(
            text(
                "INSERT INTO behavior_insights "
                "(id, user_id, insight_type, preference_delta, confidence, evidence_event_ids, status) "
                "VALUES (:id, :uid, :itype, :delta, :conf, :evidence, :status)"
            ),
            {
                "id": insight_id,
                "uid": user_id,
                "itype": "category_affinity",
                "delta": json.dumps({"category_weights": affinity}),
                "conf": confidence,
                "evidence": json.dumps([]),
                "status": "applied" if decision == "apply" else "held",
            },
        )

        if decision == "apply":
            await self.session.execute(
                text(
                    "INSERT INTO user_preferences (user_id, category_weights, version) "
                    "VALUES (:uid, :weights, 1) "
                    "ON CONFLICT (user_id) DO UPDATE SET "
                    "category_weights = :weights, version = user_preferences.version + 1"
                ),
                {"uid": user_id, "weights": json.dumps(affinity)},
            )

        await self.session.commit()
        logger.info(
            "feedback_cycle_done",
            user_id=str(user_id),
            decision=decision,
            confidence=confidence,
        )
        return {"decision": decision, "confidence": confidence, "insight_id": str(insight_id)}
