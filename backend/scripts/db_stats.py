import asyncio

from sqlalchemy import text

from app.infrastructure.database import async_session_factory


async def stats():
    async with async_session_factory() as s:
        docs = (await s.execute(text("SELECT count(*) FROM raw_documents"))).scalar()
        exts = (
            await s.execute(text("SELECT status, count(*) FROM extraction_results GROUP BY status"))
        ).fetchall()
        total_opps = (await s.execute(text("SELECT count(*) FROM opportunities"))).scalar()
        print(f"raw_documents: {docs}")
        print("extraction:", exts)
        print("opportunities total:", total_opps)
        titles = (
            await s.execute(
                text("SELECT title, end_date, category FROM opportunities ORDER BY created_at DESC LIMIT 10")
            )
        ).fetchall()
        for t, d, c in titles:
            print(f"  - [{c}] {t[:55]} | {d}")


asyncio.run(stats())
