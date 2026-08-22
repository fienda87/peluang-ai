import json
import uuid
from collections import Counter

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.logging import get_logger

logger = get_logger("behavior")

VALID_EVENTS = {"view", "save", "click", "apply", "expire", "win", "remove", "feedback", "ignore", "reject"}


class BehaviorService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_event(
        self,
        user_id: uuid.UUID,
        event_type: str,
        opportunity_id: uuid.UUID | None = None,
        recommendation_id: uuid.UUID | None = None,
        metadata: dict | None = None,
    ) -> uuid.UUID:
        if event_type not in VALID_EVENTS:
            raise ValueError(f"Invalid event type: {event_type}")

        event_id = uuid.uuid4()
        await self.session.execute(
            text(
                "INSERT INTO user_events (id, user_id, event_type, opportunity_id, recommendation_id, metadata) "
                "VALUES (:id, :uid, :etype, :oid, :rid, :meta)"
            ),
            {
                "id": event_id,
                "uid": user_id,
                "etype": event_type,
                "oid": opportunity_id,
                "rid": recommendation_id,
                "meta": json.dumps(metadata) if metadata else None,
            },
        )
        await self.session.commit()
        logger.info("event_recorded", user_id=str(user_id), event_type=event_type)
        return event_id

    async def get_behavior_profile(self, user_id: uuid.UUID, days: int = 30) -> dict:
        result = await self.session.execute(
            text(
                "SELECT e.event_type, o.category, count(*) "
                "FROM user_events e "
                "LEFT JOIN opportunities o ON o.id = e.opportunity_id "
                "WHERE e.user_id = :uid AND e.created_at >= now() - make_interval(days => :days) "
                "GROUP BY e.event_type, o.category"
            ),
            {"uid": user_id, "days": days},
        )
        rows = result.fetchall()

        total_events = sum(r[2] for r in rows)
        event_counts: Counter = Counter()
        category_affinity: Counter = Counter()
        positive_events = {"save", "apply", "click", "win", "view"}

        for event_type, category, count in rows:
            event_counts[event_type] += count
            if category and event_type in positive_events:
                category_affinity[category] += count

        total_positive = sum(category_affinity.values())
        affinity = (
            {cat: round(cnt / total_positive, 3) for cat, cnt in category_affinity.items()}
            if total_positive > 0
            else {}
        )

        return {
            "user_id": str(user_id),
            "total_events": total_events,
            "event_counts": dict(event_counts),
            "category_affinity": affinity,
            "window_days": days,
        }
