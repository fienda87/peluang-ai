"""Backfill embeddings untuk semua opportunity + user profile test."""
import asyncio
import uuid

from sqlalchemy import text

from app.infrastructure.database import async_session_factory
from app.modules.embedding.service import EmbeddingService


async def main():
    async with async_session_factory() as session:
        rows = await session.execute(text("SELECT id FROM opportunities"))
        ids = [r[0] for r in rows.fetchall()]
        svc = EmbeddingService(session)
        result = await svc.embed_opportunities(ids)
        await session.commit()
        print(f"opportunities embedded: {len(result)}/{len(ids)}")

        u = await session.execute(text("SELECT id FROM users LIMIT 1"))
        uid = u.scalar()
        if uid:
            await svc.embed_user_profile(uuid.UUID(str(uid)))
            await session.commit()
            print(f"profile embedded: {uid}")

    # verifikasi cosine antar opportunity via pgvector
    async with async_session_factory() as session:
        v = await session.execute(
            text(
                "SELECT o1.title, o2.title, o1.embedding <=> o2.embedding AS dist "
                "FROM opportunities o1 JOIN opportunities o2 ON o1.id != o2.id "
                "WHERE o1.embedding IS NOT NULL AND o2.embedding IS NOT NULL "
                "ORDER BY dist ASC LIMIT 3"
            )
        )
        for t1, t2, d in v.fetchall():
            print(f"sim {1-float(d):.2f} | {t1[:30]} <-> {t2[:30]}")


asyncio.run(main())
