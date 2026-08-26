import asyncio
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_session
from app.shared.config import get_agent_budget
from app.shared.eventbus import history, publish, subscribe, unsubscribe

router = APIRouter(prefix="/pipeline", tags=["stream"])


@router.get("/stream")
async def stream():
    async def gen():
        q = await subscribe()
        try:
            for event in history(80):
                payload = (
                    event
                    if isinstance(event, str)
                    else json.dumps(event, ensure_ascii=False, default=str)
                )
                yield f"data: {payload}\n\n"
            while True:
                try:
                    data = await asyncio.wait_for(q.get(), timeout=15)
                    yield f"data: {data}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            unsubscribe(q)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
@router.get("/agents/status")
async def agents_status(session: AsyncSession = Depends(get_session)):
    agents = ["discovery", "extraction", "recovery", "recommendation", "feedback"]
    out = []
    for agent in agents:
        budget = get_agent_budget(agent)
        max_steps = int(budget.get("max_steps", 8))
        max_llm = int(budget.get("max_llm_calls", 2))

        rows = await session.execute(
            text(
                "SELECT status, step_count, llm_call_count, started_at "
                "FROM agent_runs WHERE agent_type = :a "
                "ORDER BY started_at DESC LIMIT 1"
            ),
            {"a": agent},
        )
        last = rows.fetchone()

        agg = await session.execute(
            text(
                "SELECT count(*), "
                "count(*) FILTER (WHERE status IN ('success','valid')) "
                "FROM agent_runs WHERE agent_type = :a "
                "AND started_at > now() - interval '24 hours'"
            ),
            {"a": agent},
        )
        total_24h, ok_24h = agg.fetchone()

        out.append(
            {
                "agent": agent,
                "runs_24h": total_24h or 0,
                "success_rate": round((ok_24h / total_24h), 2) if total_24h else None,
                "last": {
                    "status": last[0] if last else None,
                    "steps": last[1] if last else 0,
                    "max_steps": max_steps,
                    "llm": last[2] if last else 0,
                    "max_llm": max_llm,
                    "started_at": str(last[3]) if last else None,
                },
            }
        )
    return {"agents": out}


@router.post("/test-event")
async def test_event(msg: str = "Tes event dari API"):
    publish("info", msg)
    return {"published": True}
