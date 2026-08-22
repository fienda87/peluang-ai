import uuid

from app.shared.logging import get_logger

logger = get_logger("tasks")


async def crawl_source_task(ctx: dict, source_id: uuid.UUID) -> dict:
    logger.info("crawl_source_task", source_id=str(source_id))
    return {"status": "ok", "task": "crawl_source", "source_id": str(source_id)}


async def extract_document_task(ctx: dict, raw_document_id: uuid.UUID) -> dict:
    logger.info("extract_document_task", raw_document_id=str(raw_document_id))
    return {"status": "ok", "task": "extract_document", "raw_document_id": str(raw_document_id)}


async def recover_extraction_task(ctx: dict, extraction_result_id: uuid.UUID) -> dict:
    logger.info("recover_extraction_task", extraction_result_id=str(extraction_result_id))
    return {
        "status": "ok",
        "task": "recover_extraction",
        "extraction_result_id": str(extraction_result_id),
    }


async def deduplicate_opportunity_task(ctx: dict, opportunity_id: uuid.UUID) -> dict:
    logger.info("deduplicate_opportunity_task", opportunity_id=str(opportunity_id))
    return {
        "status": "ok",
        "task": "deduplicate_opportunity",
        "opportunity_id": str(opportunity_id),
    }


async def generate_recommendation_task(ctx: dict, user_id: uuid.UUID | None = None) -> dict:
    logger.info("generate_recommendation_task", user_id=str(user_id) if user_id else "all")
    return {"status": "ok", "task": "generate_recommendation"}


async def feedback_agent_task(ctx: dict, user_id: uuid.UUID | None = None) -> dict:
    logger.info("feedback_agent_task", user_id=str(user_id) if user_id else "all")
    return {"status": "ok", "task": "feedback_agent"}


async def dispatch_notifications_task(ctx: dict) -> dict:
    logger.info("dispatch_notifications_task")
    return {"status": "ok", "task": "dispatch_notifications"}
