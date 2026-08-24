import asyncio
import uuid

from sqlalchemy import text

from app.infrastructure.database import async_session_factory
from app.modules.recommendation.service import RecommendationService


async def t():
    async with async_session_factory() as s:
        uid = (await s.execute(text("SELECT id FROM users LIMIT 1"))).scalar()
        await RecommendationService(s).generate(uuid.UUID(str(uid)), trigger="on_demand")
        feed = await RecommendationService(s).get_feed(uuid.UUID(str(uid)), limit=5)
        for f in feed:
            print(f"{f['score']:.3f} [{f['category']}] {f['title'][:45]}")


asyncio.run(t())
