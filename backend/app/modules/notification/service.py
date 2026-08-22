import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.logging import get_logger

logger = get_logger("notification")


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def schedule_deadline_reminders(self) -> int:
        result = await self.session.execute(
            text(
                "SELECT DISTINCT ue.user_id, ue.opportunity_id, o.end_date, o.title "
                "FROM user_events ue "
                "JOIN opportunities o ON o.id = ue.opportunity_id "
                "WHERE ue.event_type IN ('save', 'apply') "
                "AND o.status = 'active' AND o.end_date IS NOT NULL"
            )
        )
        rows = result.fetchall()
        scheduled = 0
        now = datetime.now(timezone.utc)

        for user_id, opp_id, end_date, title in rows:
            days_left = (end_date - now.date()).days
            if days_left not in (3, 1):
                continue

            ntype = "deadline_d3" if days_left == 3 else "deadline_d1"
            idem_key = f"{user_id}:{opp_id}:{ntype}:{end_date.isoformat()}"

            try:
                await self.session.execute(
                    text(
                        "INSERT INTO notifications "
                        "(id, user_id, opportunity_id, notification_type, channel, status, "
                        "idempotency_key, payload, scheduled_at) "
                        "VALUES (:id, :uid, :oid, :ntype, 'telegram', 'scheduled', :idem, :payload, now())"
                    ),
                    {
                        "id": uuid.uuid4(),
                        "uid": user_id,
                        "oid": opp_id,
                        "ntype": ntype,
                        "idem": idem_key,
                        "payload": json.dumps({"title": title, "days_left": days_left}),
                    },
                )
                scheduled += 1
            except Exception:
                pass

        await self.session.commit()
        logger.info("reminders_scheduled", count=scheduled)
        return scheduled

    async def dispatch_due(self, limit: int = 100) -> int:
        result = await self.session.execute(
            text(
                "SELECT id, user_id, notification_type, payload FROM notifications "
                "WHERE status = 'scheduled' AND scheduled_at <= now() "
                "ORDER BY scheduled_at ASC LIMIT :limit"
            ),
            {"limit": limit},
        )
        rows = result.fetchall()
        sent = 0

        for notif_id, user_id, ntype, payload in rows:
            await self.session.execute(
                text(
                    "UPDATE notifications SET status = 'sent', sent_at = now() WHERE id = :id"
                ),
                {"id": notif_id},
            )
            sent += 1
            logger.info("notification_sent", notif_id=str(notif_id), type=ntype)

        await self.session.commit()
        return sent

    async def cancel_notification(self, notification_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            text(
                "UPDATE notifications SET status = 'cancelled' "
                "WHERE id = :id AND status = 'scheduled' RETURNING id"
            ),
            {"id": notification_id},
        )
        await self.session.commit()
        return result.scalar_one_or_none() is not None
