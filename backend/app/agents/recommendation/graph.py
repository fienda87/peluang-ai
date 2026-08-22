from typing import Any

from langgraph.graph import END, StateGraph
from pydantic import BaseModel

from app.shared.logging import get_logger

logger = get_logger("recommendation.agent")


class RecommendationState(BaseModel):
    user_id: str
    candidates: list[dict[str, Any]] = []
    ranked: list[dict[str, Any]] = []
    explanations: dict[str, str] = {}
    step_count: int = 0
    llm_call_count: int = 0
    current_state: str = "START"
    status: str = "running"
    error: str | None = None


def node_user_context(state: RecommendationState) -> RecommendationState:
    state.step_count += 1
    state.current_state = "USER_CONTEXT"
    return state


def node_get_candidates(state: RecommendationState) -> RecommendationState:
    state.step_count += 1
    state.current_state = "GET_CANDIDATES"
    return state


def node_rank(state: RecommendationState) -> RecommendationState:
    state.step_count += 1
    state.current_state = "RANK"
    state.ranked = sorted(state.candidates, key=lambda c: c.get("score", 0), reverse=True)[:20]
    return state


def node_contextual_reorder(state: RecommendationState) -> RecommendationState:
    state.step_count += 1
    state.current_state = "CONTEXTUAL_REORDER"
    eligible_first = [c for c in state.ranked if c.get("eligibility") == "ELIGIBLE"]
    unknown = [c for c in state.ranked if c.get("eligibility") == "UNKNOWN"]
    ineligible = [c for c in state.ranked if c.get("eligibility") == "INELIGIBLE"]
    state.ranked = eligible_first + unknown
    if ineligible:
        logger.warning("ineligible_filtered", count=len(ineligible))
    return state


def node_explain(state: RecommendationState) -> RecommendationState:
    state.step_count += 1
    state.current_state = "EXPLAIN"
    for c in state.ranked[:5]:
        opp_id = c.get("opportunity_id", "")
        state.explanations[opp_id] = (
            f"Rekomendasi berdasarkan kecocokan kategori dan tenggat waktu. "
            f"Skor: {c.get('score', 0):.2f}"
        )
    return state


def node_persist(state: RecommendationState) -> RecommendationState:
    state.step_count += 1
    state.current_state = "PERSIST"
    state.status = "success"
    return state


def build_recommendation_graph():
    graph = StateGraph(RecommendationState)

    graph.add_node("user_context", node_user_context)
    graph.add_node("get_candidates", node_get_candidates)
    graph.add_node("rank", node_rank)
    graph.add_node("contextual_reorder", node_contextual_reorder)
    graph.add_node("explain", node_explain)
    graph.add_node("persist", node_persist)

    graph.set_entry_point("user_context")
    graph.add_edge("user_context", "get_candidates")
    graph.add_edge("get_candidates", "rank")
    graph.add_edge("rank", "contextual_reorder")
    graph.add_edge("contextual_reorder", "explain")
    graph.add_edge("explain", "persist")
    graph.add_edge("persist", END)

    return graph.compile()
