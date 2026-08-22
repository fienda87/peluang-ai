from typing import Any

from langgraph.graph import END, StateGraph
from pydantic import BaseModel

from app.shared.logging import get_logger

logger = get_logger("feedback.agent")

CONFIDENCE_THRESHOLD = 0.7
MIN_EVENTS = 5


class FeedbackState(BaseModel):
    user_id: str
    behavior_profile: dict[str, Any] = {}
    patterns: dict[str, Any] = {}
    signal_quality: str = "unknown"
    preference_delta: dict[str, Any] = {}
    confidence: float = 0.0
    evidence_event_ids: list[str] = []
    decision: str = "pending"
    step_count: int = 0
    llm_call_count: int = 0
    current_state: str = "START"
    status: str = "running"


def node_load_behavior(state: FeedbackState) -> FeedbackState:
    state.step_count += 1
    state.current_state = "LOAD_BEHAVIOR"
    return state


def node_summarize_patterns(state: FeedbackState) -> FeedbackState:
    state.step_count += 1
    state.current_state = "SUMMARIZE_PATTERNS"
    affinity = state.behavior_profile.get("category_affinity", {})
    state.patterns = {"category_affinity": affinity}
    return state


def node_check_signal_quality(state: FeedbackState) -> FeedbackState:
    state.step_count += 1
    state.current_state = "CHECK_SIGNAL_QUALITY"
    total = state.behavior_profile.get("total_events", 0)
    if total < MIN_EVENTS:
        state.signal_quality = "insufficient"
    elif len(state.patterns.get("category_affinity", {})) >= 2:
        state.signal_quality = "strong"
    else:
        state.signal_quality = "weak"
    return state


def node_propose_update(state: FeedbackState) -> FeedbackState:
    state.step_count += 1
    state.current_state = "PROPOSE_PREFERENCE_UPDATE"

    if state.signal_quality == "insufficient":
        state.decision = "no_update"
        state.status = "success"
        return state

    affinity = state.patterns.get("category_affinity", {})
    if not affinity:
        state.decision = "no_update"
        state.status = "success"
        return state

    state.preference_delta = {"category_weights": affinity}
    state.confidence = 0.8 if state.signal_quality == "strong" else 0.5
    return state


def node_validate(state: FeedbackState) -> FeedbackState:
    state.step_count += 1
    state.current_state = "VALIDATE"
    if state.decision == "no_update":
        state.status = "success"
    elif state.confidence >= CONFIDENCE_THRESHOLD:
        state.decision = "apply"
        state.status = "success"
    else:
        state.decision = "hold"
        state.status = "success"
    return state


def build_feedback_graph():
    graph = StateGraph(FeedbackState)

    graph.add_node("load_behavior", node_load_behavior)
    graph.add_node("summarize_patterns", node_summarize_patterns)
    graph.add_node("check_signal_quality", node_check_signal_quality)
    graph.add_node("propose_update", node_propose_update)
    graph.add_node("validate", node_validate)

    graph.set_entry_point("load_behavior")
    graph.add_edge("load_behavior", "summarize_patterns")
    graph.add_edge("summarize_patterns", "check_signal_quality")
    graph.add_edge("check_signal_quality", "propose_update")
    graph.add_edge("propose_update", "validate")
    graph.add_edge("validate", END)

    return graph.compile()
