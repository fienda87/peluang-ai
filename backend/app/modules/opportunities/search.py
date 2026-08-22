from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.logging import get_logger

logger = get_logger("opportunities.search")


class SearchService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def search(
        self,
        q: str | None = None,
        category: str | None = None,
        location: str | None = None,
        date_after: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        conditions = ["status = 'active'"]
        params: dict = {"limit": limit, "offset": offset}

        if q:
            conditions.append("(title ILIKE :q OR description ILIKE :q)")
            params["q"] = f"%{q}%"
        if category:
            conditions.append("category = :category")
            params["category"] = category
        if location:
            conditions.append("location ILIKE :location")
            params["location"] = f"%{location}%"
        if date_after:
            conditions.append("(end_date IS NULL OR end_date >= :date_after)")
            params["date_after"] = date_after

        where = " AND ".join(conditions)
        result = await self.session.execute(
            text(
                f"SELECT id, title, slug, category, organizer, location, end_date, prize "
                f"FROM opportunities WHERE {where} "
                f"ORDER BY end_date ASC NULLS LAST LIMIT :limit OFFSET :offset"
            ),
            params,
        )
        rows = result.fetchall()
        return [
            {
                "id": str(r[0]),
                "title": r[1],
                "slug": r[2],
                "category": r[3],
                "organizer": r[4],
                "location": r[5],
                "end_date": str(r[6]) if r[6] else None,
                "prize": r[7],
            }
            for r in rows
        ]
