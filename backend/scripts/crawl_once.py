"""Run one full crawl cycle synchronously: crawl sources → extract → persist.

Usage:
    python -m scripts.crawl_once                # semua source aktif
    python -m scripts.crawl_once --source lpdp  # by nama (substring, case-insensitive)
"""
import argparse
import asyncio
import uuid

from sqlalchemy import text

from app.infrastructure import get_storage
from app.infrastructure.database import async_session_factory
from app.modules.ingestion.pipeline import CrawlPipeline
from app.modules.ingestion.processing import process_document
from app.shared.logging import get_logger, setup_logging

setup_logging()
logger = get_logger("crawl_once")


async def run(source_filter: str | None) -> None:
    async with async_session_factory() as session:
        if source_filter:
            rows = await session.execute(
                text(
                    "SELECT id, name FROM sources "
                    "WHERE is_active = TRUE AND name ILIKE :pat"
                ),
                {"pat": f"%{source_filter}%"},
            )
        else:
            rows = await session.execute(
                text("SELECT id, name FROM sources WHERE is_active = TRUE")
            )
        sources = rows.fetchall()

    if not sources:
        print("Tidak ada source aktif yang cocok.")
        return

    print(f"Menjalankan crawl untuk {len(sources)} source...\n")
    totals = {"docs": 0, "opps": 0, "errors": 0}

    for src_id, src_name in sources:
        print(f"=== {src_name} ===")
        async with async_session_factory() as session:
            pipeline = CrawlPipeline(session, get_storage())
            result = await pipeline.crawl(uuid.UUID(str(src_id)))

        new_docs = result.get("new_documents", [])
        status = result.get("status")
        print(f"  crawl: {status}, halaman={result.get('pages_found')}, dok baru={len(new_docs)}")

        for doc_id in new_docs:
            async with async_session_factory() as session:
                try:
                    proc = await process_document(session, uuid.UUID(doc_id), redis=None)
                except Exception as e:
                    totals["errors"] += 1
                    print(f"    EXCEPTION: {str(e)[:150]}")
                    continue
            if proc["status"] == "ok":
                if proc.get("opportunity_id"):
                    totals["opps"] += 1
                    print(
                        f"    [{proc['strategy']}] conf={proc['confidence']} "
                        f"llm={proc['llm_calls']} → opp {proc['opportunity_id'][:8]}"
                    )
                else:
                    print(f"    [{proc['strategy']}] status={proc['extraction_status']} (no opp)")
            else:
                totals["errors"] += 1
                print(f"    ERROR: {proc.get('reason')}")

        totals["docs"] += len(new_docs)
        print()

    print("=" * 40)

    # Recovery: proses raw_documents yang belum punya extraction_results
    async with async_session_factory() as session:
        pending = await session.execute(
            text(
                "SELECT rd.id FROM raw_documents rd "
                "LEFT JOIN extraction_results er ON er.raw_document_id = rd.id "
                "WHERE er.id IS NULL"
            )
        )
        pending_ids = [str(r[0]) for r in pending.fetchall()]

    if pending_ids:
        print(f"Recovery: {len(pending_ids)} dokumen belum terekstrak, memproses...")
        for doc_id in pending_ids:
            async with async_session_factory() as session:
                try:
                    proc = await process_document(session, uuid.UUID(doc_id), redis=None)
                except Exception as e:
                    totals["errors"] += 1
                    print(f"  EXCEPTION: {str(e)[:150]}")
                    continue
            if proc["status"] == "ok" and proc.get("opportunity_id"):
                totals["opps"] += 1
                print(
                    f"  [{proc['strategy']}] conf={proc['confidence']} "
                    f"llm={proc['llm_calls']} → opp {proc['opportunity_id'][:8]}"
                )
            elif proc["status"] != "ok":
                totals["errors"] += 1

    print(
        f"SELESAI: {totals['docs']} dokumen baru, "
        f"{totals['opps']} opportunity dibuat, {totals['errors']} error"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=None, help="filter nama source")
    args = parser.parse_args()
    asyncio.run(run(args.source))
