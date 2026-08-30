from arq import cron
from arq.connections import RedisSettings

from app.shared.config import get_settings
from app.shared.logging import get_logger, setup_logging
from app.workers.tasks import (
    crawl_source_task,
    deduplicate_opportunity_task,
    discovery_agent_task,
    dispatch_notifications_task,
    expire_opportunities_task,
    extract_document_task,
    feedback_agent_task,
    generate_recommendation_task,
    recover_extraction_task,
    recover_pending_task,
    retention_purge_task,
)

setup_logging()
logger = get_logger("worker")


async def on_startup(ctx: dict) -> None:
    logger.info("worker_started")


async def on_shutdown(ctx: dict) -> None:
    logger.info("worker_stopped")


class WorkerSettings:
    functions = [
        crawl_source_task,
        extract_document_task,
        recover_extraction_task,
        recover_pending_task,
        deduplicate_opportunity_task,
        generate_recommendation_task,
        feedback_agent_task,
        discovery_agent_task,
        dispatch_notifications_task,
        expire_opportunities_task,
        retention_purge_task,
    ]
    cron_jobs = [
        cron(generate_recommendation_task, hour=6, minute=0),
        cron(dispatch_notifications_task, hour=7, minute=0),
        cron(recover_pending_task, hour=7, minute=30),
        cron(discovery_agent_task, weekday="sun", hour=5, minute=0),
        cron(expire_opportunities_task, hour=1, minute=0),
        cron(retention_purge_task, day=1, hour=3, minute=0),
    ]
    on_startup = on_startup
    on_shutdown = on_shutdown
    max_jobs = 10
    job_timeout = 300
    retry_jobs = True
    max_tries = 3
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
