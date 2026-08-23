"""Backfill dedup decisions + embeddings for opportunities missing them."""
import asyncio
import uuid

from sqlalchemy import text

from app.infrastructure.database import async_session_factory
from app.modules.ai import get_ai
from app.modules.deduplication.service import DeduplicationService
from app.modules.embedding.service import EmbeddingService
from app.shared.logging import setup_logging

setup_logging()


async def main():
    async with async_session_factory() as session:
        rows = await session.execute(
            text(
                "SELECT o.id FROM opportunities o "
                "LEFT JOIN dedup_decisions d ON d.opportunity_id = o.id "
                "WHERE d.id IS NULL"
            )
        )
        opp_ids = [str(r[0]) for r in rows.fetchall()]

    print(f"{len(opp_ids)} opportunity tanpa dedup decision")
    for oid in opp_ids:
        async with async_session_factory() as session:
            try:
                svc = DeduplicationService(session)
                await svc.mark_canonical(oid)
                await session.commit()
                try:
                    await EmbeddingService(session, get_ai()).embed_opportunities([uuid.UUID(oid)])
                    await session.commit()
                except Exception as e:
                    print(f"  embed skip {oid[:8]}: {str(e)[:80]}")
                print(f"  canonical+embed ok {oid[:8]}")
            except Exception as e:
                print(f"  FAIL {oid[:8]}: {str(e)[:100]}")


asyncio.run(main())
