import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.infrastructure import get_storage
from app.infrastructure.database import engine
from app.modules.ai import get_ai
from app.modules.deduplication.service import DeduplicationService
from app.modules.extraction.validation import ValidationService
from app.modules.extraction.vision_service import VisionExtractionService
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
    logger.info("recover_extraction_task_start", extraction_id=extraction_result_id)
    ext_uuid = uuid.UUID(extraction_result_id)

    async with async_session_factory() as session:
        from sqlalchemy import text

        result = await session.execute(
            text("SELECT raw_document_id FROM extraction_results WHERE id = :id"),
            {"id": ext_uuid},
        )
        row = result.one_or_none()

        if not row:
            logger.error("extraction_not_found", extraction_id=extraction_result_id)
            return {"status": "error", "reason": "extraction_not_found"}

        raw_doc_id = row[0]

        vision_svc = VisionExtractionService(get_ai())
        doc_result = await session.execute(
            text("SELECT file_url FROM raw_documents WHERE id = :id"),
            {"id": raw_doc_id},
        )
        doc_row = doc_result.one_or_none()

        if doc_row:
            storage = get_storage()
            try:
                image_bytes = await storage.get(doc_row[0])
                vision_result = await vision_svc.extract_from_image(image_bytes)

                if vision_result:
                    validation_svc = ValidationService()
                    confidence = validation_svc.compute_overall_confidence(vision_result)
                    status = "recovered"

                    import json

                    await session.execute(
                        text(
                            "UPDATE extraction_results SET extracted_data = :data, overall_confidence = :conf, "
                            "status = :status WHERE id = :id"
                        ),
                        {
                            "id": ext_uuid,
                            "data": json.dumps(vision_result.to_dict()),
                            "conf": confidence,
                            "status": status,
                        },
                    )
                    await session.commit()
                    logger.info("extraction_recovered", extraction_id=extraction_result_id, confidence=confidence)
                    return {"status": "ok", "recovery": "success", "confidence": confidence}
            except Exception as e:
                logger.error("recovery_failed", extraction_id=extraction_result_id, error=str(e))

    logger.info("recovery_incomplete", extraction_id=extraction_result_id)
    return {"status": "ok", "recovery": "failed"}


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
    logger.info("recommendation_task_start", user_id=user_id)
    from app.modules.recommendation.service import RecommendationService

    async with async_session_factory() as session:
        svc = RecommendationService(session)
        if user_id:
            result = await svc.generate(uuid.UUID(user_id), trigger="cron")
            return {"status": "ok", "result": result}

        result = await session.execute(text("SELECT id FROM users WHERE is_active = TRUE"))
        users = [row[0] for row in result.fetchall()]
        total = 0
        for uid in users:
            await svc.generate(uid, trigger="cron")
            total += 1
        return {"status": "ok", "users_processed": total}


async def feedback_agent_task(ctx: dict, user_id: str | None = None) -> dict:
    logger.info("feedback_agent_task_start", user_id=user_id)
    from app.modules.behavior.feedback_service import FeedbackService

    async with async_session_factory() as session:
        svc = FeedbackService(session)
        if user_id:
            result = await svc.run_feedback_cycle(uuid.UUID(user_id))
            return {"status": "ok", "result": result}

        result = await session.execute(text("SELECT id FROM users WHERE is_active = TRUE"))
        users = [row[0] for row in result.fetchall()]
        processed = 0
        for uid in users:
            await svc.run_feedback_cycle(uid)
            processed += 1
        return {"status": "ok", "users_processed": processed}


async def dispatch_notifications_task(ctx: dict) -> dict:
    logger.info("dispatch_notifications_task_start")
    from app.modules.notification.service import NotificationService

    async with async_session_factory() as session:
        svc = NotificationService(session)
        scheduled = await svc.schedule_deadline_reminders()
        sent = await svc.dispatch_due()
        return {"status": "ok", "scheduled": scheduled, "sent": sent}


async def retention_purge_task(ctx: dict) -> dict:
    logger.info("retention_purge_task_start")
    from app.modules.analytics.retention import RetentionService

    async with async_session_factory() as session:
        results = await RetentionService(session).purge_old_data()
        return {"status": "ok", "purged": results}
