import asyncio
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx

from app.shared.config import get_app_config
from app.shared.logging import get_logger

logger = get_logger("ingestion.html")

USER_AGENT = "PeluangAI/0.1 (opportunity indexer; +https://peluang.ai)"


@dataclass
class FetchResult:
    url: str
    content: bytes
    content_type: str
    status_code: int
    success: bool
    error: str | None = None


class HTMLFetcher:
    def __init__(self) -> None:
        cfg = get_app_config().get("ingestion", {})
        self.max_concurrent = cfg.get("max_concurrent_requests", 20)
        self.timeout_s = cfg.get("request_timeout_s", 30)
        self.respect_robots = cfg.get("respect_robots_txt", True)
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        self._robots_cache: dict[str, RobotFileParser] = {}

    async def _get_robots(self, client: httpx.AsyncClient, url: str) -> RobotFileParser:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if base not in self._robots_cache:
            rp = RobotFileParser()
            robots_url = f"{base}/robots.txt"
            try:
                resp = await client.get(robots_url, timeout=10)
                if resp.status_code == 200:
                    rp.parse(resp.text.splitlines())
                else:
                    rp.parse([])
            except httpx.HTTPError:
                rp.parse([])
            self._robots_cache[base] = rp
        return self._robots_cache[base]

    async def fetch(self, url: str) -> FetchResult:
        async with self._semaphore:
            try:
                async with httpx.AsyncClient(
                    follow_redirects=True, timeout=self.timeout_s
                ) as client:
                    if self.respect_robots:
                        rp = await self._get_robots(client, url)
                        if not rp.can_fetch(USER_AGENT, url):
                            logger.info("blocked_by_robots", url=url)
                            return FetchResult(
                                url=url, content=b"", content_type="",
                                status_code=0, success=False, error="BLOCKED_BY_ROBOTS",
                            )
                    resp = await client.get(url, headers={"User-Agent": USER_AGENT})
                    return FetchResult(
                        url=str(resp.url),
                        content=resp.content,
                        content_type=resp.headers.get("content-type", ""),
                        status_code=resp.status_code,
                        success=resp.status_code == 200,
                        error=None if resp.status_code == 200 else f"HTTP_{resp.status_code}",
                    )
            except httpx.TimeoutException:
                return FetchResult(
                    url=url, content=b"", content_type="",
                    status_code=0, success=False, error="TIMEOUT",
                )
            except httpx.HTTPError as e:
                return FetchResult(
                    url=url, content=b"", content_type="",
                    status_code=0, success=False, error=f"NETWORK_ERROR: {e}",
                )

    async def fetch_many(self, urls: list[str]) -> list[FetchResult]:
        tasks = [self.fetch(url) for url in urls]
        return await asyncio.gather(*tasks)

    def extract_links(self, html: str, base_url: str) -> list[str]:
        import re

        hrefs = re.findall(r'href=["\']([^"\']+)["\']', html)
        links = []
        for href in hrefs:
            absolute = urljoin(base_url, href)
            parsed = urlparse(absolute)
            if parsed.scheme in ("http", "https"):
                links.append(absolute.split("#")[0])
        return list(dict.fromkeys(links))
