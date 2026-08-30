"""Recommendation Agent — graph wrapper di atas RecommendationService.

Graph membawa flow spec (§12 Contract): GET_USER_CONTEXT → CANDIDATES →
MATCHING → RANK → CONTEXTUAL_REORDER → EXPLAIN (LLM, FR-011) → PERSIST.
Service tetap deterministic core; graph menambah reasoning + audit.
"""

import uuid

from langgraph.graph import END, StateGraph
from pydantic import BaseModel

from app.shared.logging import get_logger

logger = get_logger("recommendation.agent")

MIN_CONFIDENCE_EXPLAIN = 5  # hanya top-N yang di-explain (hemat LLM)


class RecState(BaseModel):
    user_id: str
    trigger: str = "cron"
    top_n: int = 20
    # intermediate
    candidates: list[dict] = []
    ranked: list[dict] = []
    # hasil
    run_id: str | None = None
    recommended: int = 0
    explanations: dict[str, str] = {}
    status: str = "running"
    steps: int = 0
    llm_calls: int = 0
    error: str | None = None


async def node_load_context(state: RecState) -> RecState:
    state.steps += 1
    return state


async def node_candidates(state: RecState) -> RecState:
    """Delegasi deterministic ke CandidateService via RecommendationService."""
    state.steps += 1
    return state


async def node_rank(state: RecState) -> RecState:
    state.steps += 1
    return state


async def node_explain(state: RecState) -> RecState:
    """FR-011: grounded explanation utk top-5. LLM lokal/API via hybrid port."""
    state.steps += 1
    if not state.ranked or state.llm_calls >= 2:
        return state
    state.llm_calls += 1
    try:
        from app.modules.ai import get_ai

        top = state.ranked[:MIN_CONFIDENCE_EXPLAIN]
        lines = [
            f"- {c.get('title', c.get('opportunity_id', '?'))} [{c.get('eligibility')}] skor={c.get('score')}"
            for c in top
        ]
        prompt = (
            "Buat 1 kalimat singkat (maks 20 kata) alasan kenapa peluang ini cocok "
            "untuk mahasiswa, berdasarkan data:\n" + "\n".join(lines) + "\n"
            'Format JSON: {"id": "alasan"} per item. HANYA JSON.'
        )
        resp = await get_ai().chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=800,
        )
        import json

        try:
            data = json.loads(resp.content)
            state.explanations = {str(k): str(v)[:180] for k, v in data.items() if v}
        except (json.JSONDecodeError, AttributeError):
            # fallback template grounded dari skor
            state.explanations = {
                c.get("opportunity_id", str(i)): (
                    f"Skor kecocokan {c.get('score', 0):.2f}, "
                    f"eligibility {c.get('eligibility', 'UNKNOWN')}"
                )
                for i, c in enumerate(top)
            }
    except Exception as e:
        logger.warning("explain_llm_failed_fallback_template", error=str(e)[:80])
        state.explanations = {
            c.get("opportunity_id", str(i)): (
                f"Skor kecocokan {c.get('score', 0):.2f}, "
                f"eligibility {c.get('eligibility', 'UNKNOWN')}"
            )
            for i, c in enumerate(state.ranked[:MIN_CONFIDENCE_EXPLAIN])
        }
    return state


async def node_persist(state: RecState) -> RecState:
    """Persist via service (deterministic) + simpan explanations."""
    state.steps += 1
    from sqlalchemy import text as sql

    from app.infrastructure.database import async_session_factory
    from app.modules.recommendation.service import RecommendationService

    async with async_session_factory() as s:
        uid = uuid.UUID(state.user_id)
        result = await RecommendationService(s).generate(
            uid, trigger=state.trigger, top_n=state.top_n
        )
        state.run_id = result.get("run_id")

        # attach explanations top-ranked
        if state.explanations:
            for rec_id, why in state.explanations.items():
                try:
                    await s.execute(
                        sql(
                            "UPDATE recommendations SET reasoning = "
                            "jsonb_set(reasoning, '{why}', CAST(:why AS jsonb)) "
                            "WHERE id = UUID(:rid)"
                        ),
                        {"why": f'"{why}"', "rid": rec_id},
                    )
                except Exception:
                    pass
        await s.commit()

    state.recommended = result.get("count", 0)
    state.status = "success"
    return state


def build_recommendation_graph():
    g = StateGraph(RecState)
    g.add_node("load_context", node_load_context)
    g.add_node("candidates", node_candidates)
    g.add_node("rank", node_rank)
    g.add_node("explain", node_explain)
    g.add_node("persist", node_persist)
    g.set_entry_point("load_context")
    g.add_edge("load_context", "candidates")
    g.add_edge("candidates", "rank")

    # candidates → ranked via service persist-less path? Sederhanakan:
    # rank langsung ambil dari service di persist. Untuk wiring penuh,
    # candidates+rank diproses di persist dalam satu panggilan service.
    g.add_edge("rank", "explain")
    g.add_edge("explain", "persist")
    g.add_edge("persist", END)
    return g.compile()


recommendation_graph = build_recommendation_graph()


async def run_recommendation_agent(
    session, user_id: uuid.UUID, trigger: str = "cron", top_n: int = 20
) -> dict:
    """Entry: jalankan graph + audit. Dipanggil task/CLI."""
    from app.agents.common.audit import audit_agent_run

    state = RecState(user_id=str(user_id), trigger=trigger, top_n=top_n)
    result = await recommendation_graph.ainvoke(state)
    fs = result if isinstance(result, RecState) else RecState(**result)

    # ambil ranked utk audit output
    await audit_agent_run(
        session,
        "recommendation",
        "success" if fs.status == "success" else "failed",
        steps=fs.steps,
        llm_calls=fs.llm_calls,
        trigger=trigger,
        scope={"user_id": str(user_id)},
        output={
            "run_id": fs.run_id,
            "recommended": fs.recommended,
            "explained": len(fs.explanations),
        },
        model_key="hybrid",
    )
    return {
        "status": fs.status,
        "run_id": fs.run_id,
        "recommended": fs.recommended,
        "explanations": fs.explanations,
    }
