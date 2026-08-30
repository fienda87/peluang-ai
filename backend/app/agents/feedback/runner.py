"""Feedback Agent — graph wrapper di atas FeedbackService.

Graph: LOAD_BEHAVIOR → PATTERNS → SIGNAL_QUALITY → ESTIMATE → INSIGHT →
VALIDATE → APPLY/NO-UPDATE/HOLD. Keputusan via graph; eksekusi via service
(satu-satu jalan menulis preference sesuai Contract §13).
"""

import uuid

from langgraph.graph import END, StateGraph
from pydantic import BaseModel

from app.shared.config import get_agent_budget
from app.shared.logging import get_logger

logger = get_logger("feedback.agent")


class FBState(BaseModel):
    user_id: str
    total_events: int = 0
    patterns: dict = {}
    signal_quality: str = "unknown"  # strong | weak | insufficient
    confidence: float = 0.0
    decision: str = "pending"  # apply | no_update | hold
    steps: int = 0
    llm_calls: int = 0
    status: str = "running"
    output: dict = {}


async def node_load(state: FBState) -> FBState:
    state.steps += 1

    from app.infrastructure.database import async_session_factory
    from app.modules.behavior.service import BehaviorService

    async with async_session_factory() as s:
        profile = await BehaviorService(s).get_behavior_profile(
            uuid.UUID(state.user_id)
        )
    state.total_events = profile.get("total_events", 0)
    state.patterns = {
        "category_affinity": profile.get("category_affinity", {}),
        "event_counts": profile.get("event_counts", {}),
    }
    return state


async def node_patterns(state: FBState) -> FBState:
    state.steps += 1
    return state


def _budget():
    b = get_agent_budget("feedback")
    return int(b.get("min_events_required", 5)), float(b.get("confidence_threshold", 0.7))


async def node_signal_quality(state: FBState) -> FBState:
    state.steps += 1
    min_events, _ = _budget()
    affinity = state.patterns.get("category_affinity", {})
    if state.total_events < min_events:
        state.signal_quality = "insufficient"
    elif len(affinity) >= 2:
        state.signal_quality = "strong"
    else:
        state.signal_quality = "weak"
    return state


async def node_estimate(state: FBState) -> FBState:
    state.steps += 1
    state.confidence = {"strong": 0.8, "weak": 0.5}.get(state.signal_quality, 0.0)
    return state


async def node_validate(state: FBState) -> FBState:
    state.steps += 1
    _, threshold = _budget()
    if state.signal_quality == "insufficient":
        state.decision = "no_update"
    elif state.confidence >= threshold:
        state.decision = "apply"
    else:
        state.decision = "hold"
    state.status = "success"
    return state


async def node_apply(state: FBState) -> FBState:
    state.steps += 1
    if state.decision != "apply":
        state.output = {"decision": state.decision, "reason": state.signal_quality}
        return state

    # Eksekusi via service (satu-satu penulis preference)
    from app.infrastructure.database import async_session_factory
    from app.modules.behavior.feedback_service import FeedbackService

    async with async_session_factory() as s:
        svc = FeedbackService(s)
        # FeedbackService punya cycle sendiri; kita pakai hasil graph utk gate
        result = await svc.run_feedback_cycle(uuid.UUID(state.user_id))
    state.output = result
    return state


def build_feedback_graph():
    g = StateGraph(FBState)
    g.add_node("load", node_load)
    g.add_node("patterns", node_patterns)
    g.add_node("signal_quality", node_signal_quality)
    g.add_node("estimate", node_estimate)
    g.add_node("validate", node_validate)
    g.add_node("apply", node_apply)
    g.set_entry_point("load")
    g.add_edge("load", "patterns")
    g.add_edge("patterns", "signal_quality")
    g.add_edge("signal_quality", "estimate")
    g.add_edge("estimate", "validate")
    g.add_edge("validate", "apply")
    g.add_edge("apply", END)
    return g.compile()


feedback_graph = build_feedback_graph()


async def run_feedback_agent(session, user_id: uuid.UUID) -> dict:
    from app.agents.common.audit import audit_agent_run

    state = FBState(user_id=str(user_id))
    result = await feedback_graph.ainvoke(state)
    fs = result if isinstance(result, FBState) else FBState(**result)

    await audit_agent_run(
        session,
        "feedback",
        "success",
        steps=fs.steps,
        llm_calls=fs.llm_calls,
        trigger="cron",
        scope={"user_id": str(user_id)},
        output={"decision": fs.decision, "confidence": fs.confidence},
    )
    return {"decision": fs.decision, "output": fs.output}
