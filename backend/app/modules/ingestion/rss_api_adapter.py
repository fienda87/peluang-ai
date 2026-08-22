from dataclasses import dataclass

import feedparser
import httpx

from app.shared.logging import get_logger

logger = get_logger("ingestion.rss")


@dataclass
class FeedItem:
    title: str
    link: str
    summary: str
    published: str | None = None


class RSSAdapter:
    async def fetch_feed(self, url: str) -> list[FeedItem]:
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                content = resp.text
        except httpx.HTTPError as e:
            logger.error("rss_fetch_failed", url=url, error=str(e))
            return []

        feed = feedparser.parse(content)
        items = []
        for entry in feed.entries:
            items.append(
                FeedItem(
                    title=entry.get("title", ""),
                    link=entry.get("link", ""),
                    summary=entry.get("summary", ""),
                    published=entry.get("published"),
                )
            )
        logger.info("rss_fetched", url=url, count=len(items))
        return items


class APIAdapter:
    async def fetch(
        self,
        url: str,
        headers: dict | None = None,
        params: dict | None = None,
    ) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as e:
            logger.error("api_fetch_failed", url=url, error=str(e))
            return []

        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("items", "results", "data", "opportunities"):
                if key in data and isinstance(data[key], list):
                    return data[key]
            return [data]
        return []
