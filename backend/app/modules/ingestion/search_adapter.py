import httpx

from app.shared.logging import get_logger

logger = get_logger("discovery.search")


class SearchAdapter:
    def __init__(self, base_url: str = "http://localhost:8888") -> None:
        self.base_url = base_url.rstrip("/")

    async def search(self, query: str, limit: int = 10) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{self.base_url}/search",
                    params={"q": query, "format": "json"},
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as e:
            logger.error("search_failed", query=query, error=str(e))
            return []

        results = data.get("results", [])[:limit]
        return [
            {"url": r.get("url", ""), "title": r.get("title", ""), "snippet": r.get("content", "")}
            for r in results
            if r.get("url")
        ]
