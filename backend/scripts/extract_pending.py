"""Process all pending raw documents (no extraction_results yet)."""
import asyncio
import uuid

from sqlalchemy import text

from app.infrastructure.database import async_session_factory
from app.modules.ingestion.processing import process_document
from app.shared.logging import setup_logging

setup_logging()


async def main():
    async with async_session_factory() as session:
        rows = await session.execute(
            text(
                "SELECT rd.id FROM raw_documents rd "
                "LEFT JOIN extraction_results er ON er.raw_document_id = rd.id "
                "WHERE er.id IS NULL"
            )
        )
        pending = [str(r[0]) for r in rows.fetchall()]

    print(f"{len(pending)} dokumen pending")
    ok = invalid = failed = opps = 0

    for i, doc_id in enumerate(pending):
        async with async_session_factory() as session:
            try:
                r = await process_document(session, uuid.UUID(doc_id))
            except Exception as e:
                failed += 1
                print(f"[{i+1}] EXC: {str(e)[:100]}")
                continue
        if r["status"] == "ok":
            if r.get("opportunity_id"):
                opps += 1
                print(f"[{i+1}] {r['strategy']} conf={r['confidence']} -> OPP")
            elif r["extraction_status"] == "valid":
                ok += 1
            else:
                invalid += 1
        else:
            failed += 1

    print(f"SELESAI: {opps} opp baru, {ok} valid-tanpa-opp, {invalid} invalid, {failed} gagal")


asyncio.run(main())
