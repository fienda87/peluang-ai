import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.infrastructure.database import engine
from app.infrastructure.storage import get_storage
from app.modules.ai import get_ai
from app.modules.deduplication.service import DeduplicationService
from app.modules.extraction.deterministic import DeterministicExtractor
from app.modules.extraction.llm_service import LLMExtractionService
from app.modules.extraction.validation import ValidationService
from app.modules.extraction.vision_service import VisionExtractionService
from app.modules.ingestion.html_adapter import HTMLFetcher
from app.modules.ingestion.service import IngestionService
from app.shared.logging import get_logger

logger = get_logger("tasks")

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def crawl_source_task(ctx: dict, source_id: str) -> dict:
    logger.info("crawl_source_task_start", source_id=source_id)
    source_uuid = uuid.UUID(source_id)

    async with async_session_factory() as session:
        ingestion_svc = IngestionService(session, get_storage())
        fetcher = HTMLFetcher()

        run_id = await ingestion_svc.start_run(source_uuid)

        urls_found = ["https://example.com/opp1", "https://example.com/opp2"]
        results = await fetcher.fetch_many(urls_found)

        success_count = 0
        for result in results:
            if result.success:
                doc_id = await ingestion_svc.store_raw_document(
                    source_id=source_uuid,
                    doc_type="HTML",
                    content=result.content,
                    file_mime=result.content_type,
                    ingestion_run_id=run_id,
                )
                if doc_id:
                    success_count += 1

        await ingestion_svc.finish_run(
            run_id=run_id,
            status="success",
            pages_found=len(urls_found),
            documents_stored=success_count,
        )
        await session.commit()

    logger.info("crawl_source_task_done", source_id=source_id, docs=success_count)
    return {"status": "ok", "documents_stored": success_count}


async def extract_document_task(ctx: dict, raw_document_id: str) -> dict:
    logger.info("extract_document_task_start", doc_id=raw_document_id)
    doc_uuid = uuid.UUID(raw_document_id)

    async with async_session_factory() as session:
        from sqlalchemy import text

        result = await session.execute(
            text("SELECT doc_type, extracted_text FROM raw_documents WHERE id = :id"),
            {"id": doc_uuid},
        )
        row = result.one_or_none()

        if not row:
            logger.error("document_not_found", doc_id=raw_document_id)
            return {"status": "error", "reason": "document_not_found"}

        doc_type, extracted_text = row

        if not extracted_text:
            logger.warning("no_extracted_text", doc_id=raw_document_id)
            extracted_text = ""

        det_extractor = DeterministicExtractor()
        det_result = det_extractor.extract_text(extracted_text)

        llm_svc = LLMExtractionService(get_ai())
        llm_result = await llm_svc.extract_single(extracted_text)

        final_result = llm_result or det_result

        validation_svc = ValidationService()
        confidence = validation_svc.compute_overall_confidence(final_result)
        status = validation_svc.determine_status(final_result, confidence)

        import json

        extraction_id = uuid.uuid4()
        await session.execute(
            text(
                "INSERT INTO extraction_results (id, raw_document_id, strategy, extracted_data, "
                "overall_confidence, status, version) VALUES (:id, :doc_id, :strategy, :data, :conf, :status, 1)"
            ),
            {
                "id": extraction_id,
                "doc_id": doc_uuid,
                "strategy": "llm" if llm_result else "deterministic",
                "data": json.dumps(final_result.to_dict()),
                "conf": confidence,
                "status": status,
            },
        )
        await session.commit()

    logger.info("extract_document_task_done", doc_id=raw_document_id, status=status, confidence=confidence)
    return {"status": "ok", "extraction_status": status, "confidence": confidence}


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
