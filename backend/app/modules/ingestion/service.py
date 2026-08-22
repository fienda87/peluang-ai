import hashlib
import json
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.storage import StorageBackend
from app.shared.logging import get_logger

logger = get_logger("ingestion")


class IngestionService:
    def __init__(self, session: AsyncSession, storage: StorageBackend) -> None:
        self.session = session
        self.storage = storage

    async def register_source(
        self,
        name: str,
        source_type: str,
        source_url: str,
        access_method: str = "http",
        crawl_frequency: str = "daily",
        meta: dict | None = None,
    ) -> uuid.UUID:
        source_id = uuid.uuid4()
        await self.session.execute(
            text(
                "INSERT INTO sources (id, name, source_type, source_url, access_method, crawl_frequency, meta) "
                "VALUES (:id, :name, :source_type, :source_url, :access_method, :crawl_frequency, :meta::jsonb)"
            ),
            {
                "id": source_id,
                "name": name,
                "source_type": source_type,
                "source_url": source_url,
                "access_method": access_method,
                "crawl_frequency": crawl_frequency,
                "meta": json.dumps(meta or {}),
            },
        )
        await self.session.flush()
        logger.info("source_registered", source_id=str(source_id), name=name)
        return source_id

    async def start_run(self, source_id: uuid.UUID) -> uuid.UUID:
        run_id = uuid.uuid4()
        await self.session.execute(
            text(
                "INSERT INTO ingestion_runs (id, source_id, status) "
                "VALUES (:id, :source_id, 'running')"
            ),
            {"id": run_id, "source_id": source_id},
        )
        await self.session.flush()
        return run_id

    async def finish_run(
        self,
        run_id: uuid.UUID,
        status: str,
        pages_found: int = 0,
        documents_stored: int = 0,
        error_message: str | None = None,
    ) -> None:
        await self.session.execute(
            text(
                "UPDATE ingestion_runs SET status = :status, pages_found = :pages_found, "
                "documents_stored = :documents_stored, error_message = :error_message, ended_at = now() "
                "WHERE id = :id"
            ),
            {
                "id": run_id,
                "status": status,
                "pages_found": pages_found,
                "documents_stored": documents_stored,
                "error_message": error_message,
            },
        )
        await self.session.flush()

    async def store_raw_document(
        self,
        source_id: uuid.UUID,
        doc_type: str,
        content: bytes,
        file_mime: str | None = None,
        ingestion_run_id: uuid.UUID | None = None,
        meta: dict | None = None,
    ) -> uuid.UUID | None:
        checksum = hashlib.sha256(content).hexdigest()

        existing = await self.session.execute(
            text("SELECT id FROM raw_documents WHERE checksum = :checksum"),
            {"checksum": checksum},
        )
        if existing.scalar_one_or_none():
            logger.info("duplicate_document_skipped", checksum=checksum[:16])
            return None

        doc_id = uuid.uuid4()
        storage_key = f"raw/{source_id}/{doc_id}"
        file_url = await self.storage.put(storage_key, content)

        await self.session.execute(
            text(
                "INSERT INTO raw_documents (id, source_id, ingestion_run_id, doc_type, file_url, file_mime, file_size, checksum, meta) "
                "VALUES (:id, :source_id, :ingestion_run_id, :doc_type, :file_url, :file_mime, :file_size, :checksum, :meta::jsonb)"
            ),
            {
                "id": doc_id,
                "source_id": source_id,
                "ingestion_run_id": ingestion_run_id,
                "doc_type": doc_type,
                "file_url": file_url,
                "file_mime": file_mime,
                "file_size": len(content),
                "checksum": checksum,
                "meta": json.dumps(meta or {}),
            },
        )
        await self.session.flush()
        logger.info("raw_document_stored", doc_id=str(doc_id), doc_type=doc_type, size=len(content))
        return doc_id

    async def update_source_health(
        self, source_id: uuid.UUID, health_status: str, consecutive_errors: int | None = None
    ) -> None:
        if consecutive_errors is not None:
            await self.session.execute(
                text(
                    "UPDATE sources SET health_status = :health, consecutive_errors = :errors, "
                    "last_crawled_at = now() WHERE id = :id"
                ),
                {"id": source_id, "health": health_status, "errors": consecutive_errors},
            )
        else:
            await self.session.execute(
                text(
                    "UPDATE sources SET health_status = :health, last_crawled_at = now() WHERE id = :id"
                ),
                {"id": source_id, "health": health_status},
            )
        await self.session.flush()
