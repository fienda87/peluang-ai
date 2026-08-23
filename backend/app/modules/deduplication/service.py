from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.logging import get_logger

logger = get_logger("deduplication")


class DeduplicationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_duplicates(
        self,
        opportunity_id: str,
        title: str,
        url: str | None = None,
        end_date: str | None = None,
    ) -> list[tuple[str, str, float]]:
        duplicates = []

        if url:
            result = await self.session.execute(
                text("SELECT id FROM opportunities WHERE url = :url AND id != :id"),
                {"url": url, "id": opportunity_id},
            )
            url_match = result.scalar_one_or_none()
            if url_match:
                duplicates.append((url_match, "url_canonical", 0.95))

        if title and end_date:
            from datetime import date as date_cls

            if isinstance(end_date, str):
                try:
                    end_date = date_cls.fromisoformat(end_date)
                except ValueError:
                    end_date = None
            if end_date is not None:
                result = await self.session.execute(
                text(
                    "SELECT id, similarity(title, :title) as sim FROM opportunities "
                    "WHERE id != :id AND end_date = :end_date AND similarity(title, :title) > 0.8 "
                    "ORDER BY sim DESC LIMIT 1"
                ),
                {"title": title, "id": opportunity_id, "end_date": end_date},
            )
            row = result.one_or_none()
            if row:
                duplicates.append((row[0], "title_date", round(float(row[1]), 2)))

        return duplicates

    async def resolve_duplicate(
        self,
        opportunity_id: str,
        duplicate_of_id: str | None,
        method: str,
        similarity_score: float | None = None,
    ) -> None:
        await self.session.execute(
            text(
                "INSERT INTO dedup_decisions (opportunity_id, duplicate_of_id, method, similarity_score, is_duplicate) "
                "VALUES (:opp_id, :dup_id, :method, :score, :is_dup) "
                "ON CONFLICT (opportunity_id) DO UPDATE SET duplicate_of_id = :dup_id, method = :method, similarity_score = :score"
            ),
            {
                "opp_id": opportunity_id,
                "dup_id": duplicate_of_id,
                "method": method,
                "score": similarity_score,
                "is_dup": duplicate_of_id is not None,
            },
        )
        await self.session.flush()
        logger.info(
            "dedup_resolved",
            opportunity_id=opportunity_id,
            duplicate_of=duplicate_of_id,
            method=method,
            score=similarity_score,
        )

    async def mark_canonical(self, opportunity_id: str) -> None:
        await self.session.execute(
            text(
                "INSERT INTO dedup_decisions (opportunity_id, duplicate_of_id, method, is_duplicate) "
                "VALUES (:id, NULL, 'manual', FALSE) "
                "ON CONFLICT (opportunity_id) DO UPDATE SET duplicate_of_id = NULL, is_duplicate = FALSE"
            ),
            {"id": opportunity_id},
        )
        await self.session.flush()
