"""Shared agent helpers: audit row (agent_runs) — dipakai semua agent graph."""

import json
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.config import get_agent_budget
from app.shared.logging import get_logger

logger = get_logger("agents.common")


async def audit_agent_run(
    session: AsyncSession,
    agent_type: str,
    status: str,  # running | success | failed | timeout | degraded | budget_exhausted | paused
    steps: int,
    llm_calls: int,
    trigger: str = "manual",
    scope: dict | None = None,
    output: dict | None = None,
    failure_code: str | None = None,
    agent_version: str = "1.0.0",
    graph_version: str = "1.0.0",
    model_key: str | None = None,
) -> uuid.UUID:
    """Insert agent_runs audit row. Aman dipanggil setelah selesai (bukan pre-insert)."""
    run_id = uuid.uuid4()
    await session.execute(
        text(
            "INSERT INTO agent_runs (id, agent_type, agent_version, graph_version, "
            "model_key, trigger, status, user_id, source_id, opportunity_id, raw_document_id, "
            "step_count, llm_call_count, failure_code, input_summary, output_summary, "
            "started_at, ended_at, duration_ms) "
            "VALUES (:id, :atype, :aver, :gver, :model, :trigger, :status, :uid, :sid, "
            ":oid, :rid, :steps, :llm, :failure, CAST(:input AS jsonb), CAST(:output AS jsonb), "
            "now() - make_interval(secs => :dur_s), now(), :dur_ms)"
        ),
        {
            "id": run_id,
            "atype": agent_type,
            "aver": agent_version,
            "gver": graph_version,
            "model": model_key,
            "trigger": trigger,
            "status": status,
            "uid": (scope or {}).get("user_id"),
            "sid": (scope or {}).get("source_id"),
            "oid": (scope or {}).get("opportunity_id"),
            "rid": (scope or {}).get("raw_document_id"),
            "steps": steps,
            "llm": llm_calls,
            "failure": failure_code,
            "input": json.dumps(scope or {}, default=str),
            "output": json.dumps(output or {}, default=str),
            "dur_s": 0,
            "dur_ms": 0,
        },
    )
    await session.commit()  # audit harus persist langsung (runner pakai session luar)
    logger.info(
        "agent_run_audited",
        agent=agent_type,
        status=status,
        steps=steps,
        llm=llm_calls,
    )
    return run_id


def budget_of(agent: str) -> dict:
    b = get_agent_budget(agent)
    return {
        "max_steps": int(b.get("max_steps", 8)),
        "max_llm_calls": int(b.get("max_llm_calls", 2)),
        "max_runtime_s": int(b.get("max_runtime_s", 60)),
    }
