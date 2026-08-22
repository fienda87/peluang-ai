import uuid
from datetime import date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.logging import get_logger

logger = get_logger("opportunities")


def slugify(text: str) -> str:
    import re

    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text[:100]


class OpportunitiesService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_opportunity(
        self,
        source_id: uuid.UUID,
        title: str,
        category: str,
        end_date: date | str | None = None,
        organizer: str | None = None,
        location: str | None = None,
        description: str | None = None,
        prize: str | None = None,
        start_date: date | str | None = None,
        url: str | None = None,
    ) -> uuid.UUID:
        slug_base = slugify(f"{title}-{organizer or 'unknown'}")
        result = await self.session.execute(
            text("SELECT id FROM opportunities WHERE slug ILIKE :slug ORDER BY created_at DESC LIMIT 1"),
            {"slug": f"{slug_base}%"},
        )
        existing = result.scalar_one_or_none()

        if existing:
            await self.session.execute(
                text(
                    "UPDATE opportunities SET title = :title, category = :category, end_date = :end_date, "
                    "organizer = :organizer, location = :location, description = :description, "
                    "prize = :prize, start_date = :start_date, url = :url WHERE id = :id"
                ),
                {
                    "id": existing,
                    "title": title,
                    "category": category,
                    "end_date": end_date,
                    "organizer": organizer,
                    "location": location,
                    "description": description,
                    "prize": prize,
                    "start_date": start_date,
                    "url": url,
                },
            )
            await self.session.flush()
            logger.info("opportunity_updated", id=str(existing), title=title)
            return existing

        opp_id = uuid.uuid4()
        slug = f"{slug_base}-{str(opp_id)[:8]}"

        await self.session.execute(
            text(
                "INSERT INTO opportunities (id, source_id, title, slug, url, category, organizer, location, "
                "description, prize, start_date, end_date, status) "
                "VALUES (:id, :source_id, :title, :slug, :url, :category, :organizer, :location, "
                ":description, :prize, :start_date, :end_date, 'active')"
            ),
            {
                "id": opp_id,
                "source_id": source_id,
                "title": title,
                "slug": slug,
                "url": url,
                "category": category,
                "organizer": organizer,
                "location": location,
                "description": description,
                "prize": prize,
                "start_date": start_date,
                "end_date": end_date,
            },
        )
        await self.session.flush()
        logger.info("opportunity_created", id=str(opp_id), title=title)
        return opp_id

    async def add_requirements(
        self,
        opportunity_id: uuid.UUID,
        requirements: dict[str, str],
    ) -> None:
        for req_type, description in requirements.items():
            if not description:
                continue
            await self.session.execute(
                text(
                    "INSERT INTO opportunity_requirements (id, opportunity_id, req_type, description) "
                    "VALUES (:id, :opp_id, :type, :desc)"
                ),
                {"id": uuid.uuid4(), "opp_id": opportunity_id, "type": req_type, "desc": description},
            )
        await self.session.flush()

    async def set_status(self, opportunity_id: uuid.UUID, status: str) -> None:
        await self.session.execute(
            text("UPDATE opportunities SET status = :status WHERE id = :id"),
            {"status": status, "id": opportunity_id},
        )
        await self.session.flush()
