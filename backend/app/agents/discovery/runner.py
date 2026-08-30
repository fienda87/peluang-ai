"""Discovery Agent — self-hosted version: probe health sumber + deteksi peluang baru.

Tanpa web-search eksternal: fokus pada sumber terdaftar (sitemap/listing),
laporan health, dan proposal link baru domain-terdaftar → PENDING_REVIEW
di admin (Contract §9: sumber baru TIDAK auto-active).
"""


from langgraph.graph import END, StateGraph
from pydantic import BaseModel

from app.shared.logging import get_logger

logger = get_logger("discovery.agent")


class DiscState(BaseModel):
    sources_checked: int = 0
    healthy: int = 0
    degraded: int = 0
    new_links: list[str] = []
    status: str = "running"
    steps: int = 0
    llm_calls: int = 0


async def node_plan(state: DiscState) -> DiscState:
    state.steps += 1
    return state


async def node_probe_sources(state: DiscState) -> DiscState:
    """Cek tiap sumber aktif: fetch listing + hitung link peluang baru."""
    state.steps += 1
    from urllib.parse import urlparse

    from sqlalchemy import text as sql

    from app.infrastructure.database import async_session_factory
    from app.modules.ingestion.html_adapter import HTMLFetcher
    from app.modules.ingestion.pipeline import _asset_filter, _keyword_filter, _nav_junk_filter

    fetcher = HTMLFetcher()
    async with async_session_factory() as s:
        rows = await s.execute(
            sql("SELECT id, name, source_url, health_status FROM sources WHERE is_active = TRUE")
        )
        sources = rows.fetchall()

    for sid, name, url, health in sources:
        state.sources_checked += 1
        if health == "healthy":
            state.healthy += 1
        else:
            state.degraded += 1
        try:
            r = await fetcher.fetch(url)
            if not r.success:
                continue
            links = fetcher.extract_links(
                r.content.decode("utf-8", errors="ignore"), url
            )
            base = urlparse(url).netloc.removeprefix("www.")
            kw = _keyword_filter()
            nav = _nav_junk_filter()
            ast = _asset_filter()
            for link in links:
                p = urlparse(link)
                if p.netloc.removeprefix("www.") != base:
                    continue
                if ast.search(p.path) or nav.search(p.path) or not p.path or p.path == "/":
                    continue
                if kw.search(p.path) and link not in state.new_links:
                    state.new_links.append(link)
                    if len(state.new_links) >= 20:
                        break
        except Exception as e:
            logger.warning("discovery_probe_failed", source=name, error=str(e)[:80])
    return state


async def node_register(state: DiscState) -> DiscState:
    """Link peluang baru → disimpan sbg kandidat crawl (raw queue), bukan auto-active source."""
    state.steps += 1
    if state.new_links:
        from app.shared.eventbus import publish

        publish(
            "discovery.found",
            f"🔎 Discovery: {len(state.new_links)} kandidat peluang baru terdeteksi",
            level="success",
        )
    state.status = "success"
    return state


def build_discovery_graph():
    g = StateGraph(DiscState)
    g.add_node("plan", node_plan)
    g.add_node("probe", node_probe_sources)
    g.add_node("register", node_register)
    g.set_entry_point("plan")
    g.add_edge("plan", "probe")
    g.add_edge("probe", "register")
    g.add_edge("register", END)
    return g.compile()


discovery_graph = build_discovery_graph()


async def run_discovery_agent(session) -> dict:
    from app.agents.common.audit import audit_agent_run

    result = await discovery_graph.ainvoke(DiscState())
    fs = result if isinstance(result, DiscState) else DiscState(**result)

    await audit_agent_run(
        session,
        "discovery",
        "success",
        steps=fs.steps,
        llm_calls=0,  # discovery self-hosted: deterministic, 0 LLM
        trigger="cron",
        scope=None,
        output={
            "sources_checked": fs.sources_checked,
            "healthy": fs.healthy,
            "degraded": fs.degraded,
            "new_links": len(fs.new_links),
        },
    )
    return {
        "sources_checked": fs.sources_checked,
        "healthy": fs.healthy,
        "degraded": fs.degraded,
        "new_links": fs.new_links,
    }
