"""Real crawl pipeline shared by arq task and CLI."""

import uuid
from urllib.parse import urlparse

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.storage import StorageBackend
from app.modules.ingestion.health_service import SourceHealthService
from app.modules.ingestion.html_adapter import HTMLFetcher
from app.modules.ingestion.service import IngestionService
from app.shared.logging import get_logger

logger = get_logger("ingestion.pipeline")

MAX_DETAIL_PAGES = 25

ASSET_EXT_RE = None  # compiled lazily
URL_KEYWORD_RE = None  # compiled lazily


def _asset_filter():
    global ASSET_EXT_RE
    if ASSET_EXT_RE is None:
        import re

        ASSET_EXT_RE = re.compile(
            r"\.(css|js|mjs|json|xml|rss|png|jpe?g|gif|webp|svg|ico|woff2?|ttf|eot|pdf|zip)$",
            re.I,
        )
    return ASSET_EXT_RE


def _keyword_filter():
    global URL_KEYWORD_RE
    if URL_KEYWORD_RE is None:
        import re

        URL_KEYWORD_RE = re.compile(
            r"beasiswa|scholarship|lomba|kompetisi|competition|magang|intern"
            r"|fellowship|konferensi|conference|seminar|pelatihan|training"
            r"|workshop|riset|research|grant|hibah|volunteer|relawan|program",
            re.I,
        )
    return URL_KEYWORD_RE


class CrawlPipeline:
    def __init__(self, session: AsyncSession, storage: StorageBackend) -> None:
        self.session = session
        self.ingestion = IngestionService(session, storage)
        self.health = SourceHealthService(session)
        self.fetcher = HTMLFetcher()

    async def _load_source(self, source_id: uuid.UUID) -> dict | None:
        result = await self.session.execute(
            text(
                "SELECT id, name, source_url, access_method, is_active FROM sources "
                "WHERE id = :id AND is_active = TRUE"
            ),
            {"id": source_id},
        )
        row = result.one_or_none()
        if not row:
            return None
        return {
            "id": row[0],
            "name": row[1],
            "url": row[2],
            "access_method": row[3],
        }

    def _filter_links(self, links: list[str], listing_url: str) -> list[str]:
        base_domain = urlparse(listing_url).netloc.removeprefix("www.")
        kw = _keyword_filter()
        assets = _asset_filter()

        seen: set[str] = set()

        def keep(link: str) -> bool:
            parsed = urlparse(link)
            if parsed.scheme not in ("http", "https"):
                return False
            link_domain = parsed.netloc.removeprefix("www.")
            if link_domain != base_domain:
                return False
            path = parsed.path
            if assets.search(path):
                return False
            if not path or path == "/":
                return False
            return True

        filtered: list[str] = []
        for link in links:
            if link in seen or not keep(link):
                continue
            path_and_query = f"{urlparse(link).path}{urlparse(link).query}"
            if not kw.search(path_and_query):
                continue
            seen.add(link)
            filtered.append(link)
            if len(filtered) >= MAX_DETAIL_PAGES:
                break

        # Fallback: situs dengan URL tanpa keyword (mis. /p/berita.html)
        if len(filtered) < 5:
            for link in links:
                if len(filtered) >= 15:
                    break
                if link in seen or not keep(link):
                    continue
                seen.add(link)
                filtered.append(link)

        return filtered

    async def crawl(self, source_id: uuid.UUID) -> dict:
        source = await self._load_source(source_id)
        if not source:
            logger.warning("source_not_found_or_inactive", source_id=str(source_id))
            return {"status": "skipped", "reason": "not_found_or_inactive"}

        run_id = await self.ingestion.start_run(source_id)
        pages_found = 0
        new_doc_ids: list[str] = []

        try:
            listing = await self.fetcher.fetch(source["url"])
            if not listing.success or not listing.content:
                raise RuntimeError(f"listing_fetch_failed: {listing.error}")

            pages_found += 1
            links = self.fetcher.extract_links(
                listing.content.decode("utf-8", errors="ignore"), source["url"]
            )
            detail_urls = self._filter_links(links, source["url"])
            pages_found += len(detail_urls)

            logger.info(
                "crawl_listing_done",
                source=source["name"],
                links_total=len(links),
                links_relevant=len(detail_urls),
            )

            results = await self.fetcher.fetch_many(detail_urls)

            for res in results:
                if not res.success or not res.content:
                    continue
                doc_type = "HTML"
                doc_id = await self.ingestion.store_raw_document(
                    source_id=source_id,
                    doc_type=doc_type,
                    content=res.content,
                    file_mime=res.content_type.split(";")[0] if res.content_type else "text/html",
                    ingestion_run_id=run_id,
                    meta={"source_page": res.url},
                )
                if doc_id:
                    new_doc_ids.append(str(doc_id))

            await self.ingestion.finish_run(
                run_id=run_id,
                status="success" if new_doc_ids else ("partial" if results else "failed"),
                pages_found=pages_found,
                documents_stored=len(new_doc_ids),
            )
            await self.ingestion.update_source_health(source_id, "healthy", consecutive_errors=0)
            await self.session.commit()

            logger.info(
                "crawl_success",
                source=source["name"],
                pages=pages_found,
                new_docs=len(new_doc_ids),
            )
            return {
                "status": "ok",
                "source": source["name"],
                "pages_found": pages_found,
                "new_documents": new_doc_ids,
            }

        except Exception as e:
            try:
                health = await self.health.record_error(source_id)
            except Exception:
                health = "unknown"
            try:
                await self.ingestion.finish_run(
                    run_id=run_id,
                    status="failed",
                    pages_found=pages_found,
                    documents_stored=0,
                    error_message=str(e)[:500],
                )
                await self.session.commit()
            except Exception:
                pass
            logger.error("crawl_failed", source=source["name"], error=str(e), health=health)
            return {"status": "error", "source": source["name"], "reason": str(e)[:200]}
