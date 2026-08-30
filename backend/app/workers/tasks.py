import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.infrastructure import get_storage
from app.infrastructure.database import engine
from app.modules.deduplication.service import DeduplicationService
from app.modules.ingestion.pipeline import CrawlPipeline
from app.shared.logging import get_logger

logger = get_logger("tasks")

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def crawl_source_task(ctx: dict, source_id: str) -> dict:
    logger.info("crawl_source_task_start", source_id=source_id)
    source_uuid = uuid.UUID(source_id)

    async with async_session_factory() as session:
        pipeline = CrawlPipeline(session, get_storage())
        result = await pipeline.crawl(source_uuid)

    new_docs = result.get("new_documents", [])
    if ctx.get("redis") and new_docs:
        for doc_id in new_docs:
            await ctx["redis"].enqueue_job("extract_document_task", doc_id)

    logger.info(
        "crawl_source_task_done",
        source_id=source_id,
        status=result.get("status"),
        docs=len(new_docs),
    )
    return {k: v for k, v in result.items() if k != "new_documents"} | {"queued_extractions": len(new_docs)}


async def extract_document_task(ctx: dict, raw_document_id: str) -> dict:
    logger.info("extract_document_task_start", doc_id=raw_document_id)
    from app.modules.ingestion.processing import process_document

    async with async_session_factory() as session:
        result = await process_document(session, uuid.UUID(raw_document_id), redis=ctx.get("redis"))

    logger.info("extract_document_task_done", doc_id=raw_document_id, result=result)
    return result


async def recover_extraction_task(ctx: dict, extraction_result_id: str) -> dict:
    """Recovery via Recovery Agent runner (graph ladder + audit ADR-002)."""
    logger.info("recover_extraction_task_start", extraction_id=extraction_result_id)
    from sqlalchemy import text

    from app.agents.recovery.runner import run_recovery_agent

    async with async_session_factory() as session:
        r = await session.execute(
            text("SELECT raw_document_id FROM extraction_results WHERE id = :id"),
            {"id": uuid.UUID(extraction_result_id)},
        )
        raw_doc = r.scalar()
        if not raw_doc:
            return {"status": "error", "reason": "extraction_not_found"}
        result = await run_recovery_agent(session, raw_doc)
    logger.info("recover_extraction_task_done", result=result)
    return result


async def recover_pending_task(ctx: dict, limit: int = 50) -> dict:
    """Auto-trigger (§17 contract): semua needs_recovery diproses batch."""
    logger.info("recover_pending_task_start", limit=limit)
    from sqlalchemy import text

    from app.agents.recovery.runner import run_recovery_agent

    recovered = degraded = 0
    async with async_session_factory() as session:
        rows = await session.execute(
            text(
                "SELECT DISTINCT raw_document_id FROM extraction_results "
                "WHERE status = 'needs_recovery' LIMIT :lim"
            ),
            {"lim": limit},
        )
        doc_ids = [r[0] for r in rows.fetchall()]

    for doc_id in doc_ids:
        async with async_session_factory() as session:
            res = await run_recovery_agent(session, doc_id)
            if res.get("status") == "recovered":
                recovered += 1
            elif res.get("status") == "degraded":
                degraded += 1
    logger.info("recover_pending_done", total=len(doc_ids), recovered=recovered, degraded=degraded)
    return {"status": "ok", "total": len(doc_ids), "recovered": recovered, "degraded": degraded}


async def deduplicate_opportunity_task(ctx: dict, opportunity_id: str) -> dict:
    logger.info("dedup_task_start", opp_id=opportunity_id)
    opp_uuid = uuid.UUID(opportunity_id)

    async with async_session_factory() as session:
        from sqlalchemy import text

        result = await session.execute(
            text("SELECT title, url, end_date FROM opportunities WHERE id = :id"),
            {"id": opp_uuid},
        )
        row = result.one_or_none()

        if not row:
            logger.error("opportunity_not_found", opp_id=opportunity_id)
            return {"status": "error"}

        title, url, end_date = row

        dedup_svc = DeduplicationService(session)
        duplicates = await dedup_svc.find_duplicates(opportunity_id, title, url, str(end_date) if end_date else None)

        if duplicates:
            dup_id, method, score = duplicates[0]
            await dedup_svc.resolve_duplicate(opportunity_id, dup_id, method, score)
            logger.info("dedup_found", opp_id=opportunity_id, dup_count=len(duplicates))
            return {"status": "ok", "duplicates_found": len(duplicates)}
        else:
            await dedup_svc.mark_canonical(opportunity_id)
            logger.info("dedup_canonical", opp_id=opportunity_id)
            return {"status": "ok", "duplicates_found": 0}


async def generate_recommendation_task(ctx: dict, user_id: str | None = None) -> dict:
    """ADR-002 lunas: lewat Recommendation Agent graph (LangGraph + audit)."""
    logger.info("recommendation_task_start", user_id=user_id)
    from app.agents.recommendation.runner import run_recommendation_agent

    async with async_session_factory() as session:
        if user_id:
            result = await run_recommendation_agent(
                session, uuid.UUID(user_id), trigger="cron"
            )
            return {"status": "ok", "result": result}

        result = await session.execute(text("SELECT id FROM users WHERE is_active = TRUE"))
        users = [row[0] for row in result.fetchall()]
        total = 0
        for uid in users:
            await run_recommendation_agent(session, uid, trigger="cron")
            total += 1
        return {"status": "ok", "users_processed": total}


async def feedback_agent_task(ctx: dict, user_id: str | None = None) -> dict:
    """ADR-002 lunas: lewat Feedback Agent graph (LangGraph + audit)."""
    logger.info("feedback_agent_task_start", user_id=user_id)
    from app.agents.feedback.runner import run_feedback_agent

    async with async_session_factory() as session:
        if user_id:
            result = await run_feedback_agent(session, uuid.UUID(user_id))
            return {"status": "ok", "result": result}

        result = await session.execute(text("SELECT id FROM users WHERE is_active = TRUE"))
        users = [row[0] for row in result.fetchall()]
        processed = 0
        for uid in users:
            await run_feedback_agent(session, uid)
            processed += 1
        return {"status": "ok", "users_processed": processed}


async def discovery_agent_task(ctx: dict) -> dict:
    """ADR-002 lunas: Discovery Agent graph (weekly cron)."""
    logger.info("discovery_agent_task_start")
    from app.agents.discovery.runner import run_discovery_agent

    async with async_session_factory() as session:
        result = await run_discovery_agent(session)
    return {"status": "ok", "result": result}


async def dispatch_notifications_task(ctx: dict) -> dict:
    logger.info("dispatch_notifications_task_start")
    from app.modules.notification.service import NotificationService

    async with async_session_factory() as session:
        svc = NotificationService(session)
        scheduled = await svc.schedule_deadline_reminders()
        sent = await svc.dispatch_due()
        return {"status": "ok", "scheduled": scheduled, "sent": sent}


async def expire_opportunities_task(ctx: dict) -> dict:
    logger.info("expire_opportunities_task_start")
    from app.modules.opportunities.lifecycle import LifecycleService

    async with async_session_factory() as session:
        expired = await LifecycleService(session).expire_past_deadlines()
        return {"status": "ok", "expired": expired}


async def retention_purge_task(ctx: dict) -> dict:
    logger.info("retention_purge_task_start")
    from app.modules.analytics.retention import RetentionService

    async with async_session_factory() as session:
        results = await RetentionService(session).purge_old_data()
        return {"status": "ok", "purged": results}
