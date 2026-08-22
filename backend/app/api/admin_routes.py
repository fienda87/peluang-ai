import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_session

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/sources")
async def list_sources(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        text(
            "SELECT id, name, source_type, source_url, health_status, consecutive_errors, "
            "last_crawled_at, is_active FROM sources ORDER BY created_at DESC"
        )
    )
    rows = result.fetchall()
    return [
        {
            "id": str(r[0]),
            "name": r[1],
            "source_type": r[2],
            "source_url": r[3],
            "health_status": r[4],
            "consecutive_errors": r[5],
            "last_crawled_at": str(r[6]) if r[6] else None,
            "is_active": r[7],
        }
        for r in rows
    ]


@router.post("/sources/{source_id}/pause")
async def pause_source(source_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    await session.execute(
        text("UPDATE sources SET is_active = FALSE, health_status = 'paused' WHERE id = :id"),
        {"id": source_id},
    )
    await session.commit()
    return {"status": "paused", "source_id": str(source_id)}


@router.post("/sources/{source_id}/resume")
async def resume_source(source_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    await session.execute(
        text(
            "UPDATE sources SET is_active = TRUE, health_status = 'healthy', "
            "consecutive_errors = 0 WHERE id = :id"
        ),
        {"id": source_id},
    )
    await session.commit()
    return {"status": "resumed", "source_id": str(source_id)}


@router.get("/agent-runs")
async def list_agent_runs(
    agent_type: str | None = None,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
):
    if agent_type:
        result = await session.execute(
            text(
                "SELECT id, agent_type, status, step_count, llm_call_count, cost_usd, "
                "duration_ms, failure_code, started_at FROM agent_runs "
                "WHERE agent_type = :at ORDER BY started_at DESC LIMIT :limit"
            ),
            {"at": agent_type, "limit": limit},
        )
    else:
        result = await session.execute(
            text(
                "SELECT id, agent_type, status, step_count, llm_call_count, cost_usd, "
                "duration_ms, failure_code, started_at FROM agent_runs "
                "ORDER BY started_at DESC LIMIT :limit"
            ),
            {"limit": limit},
        )
    rows = result.fetchall()
    return [
        {
            "id": str(r[0]),
            "agent_type": r[1],
            "status": r[2],
            "step_count": r[3],
            "llm_call_count": r[4],
            "cost_usd": float(r[5]),
            "duration_ms": r[6],
            "failure_code": r[7],
            "started_at": str(r[8]),
        }
        for r in rows
    ]
