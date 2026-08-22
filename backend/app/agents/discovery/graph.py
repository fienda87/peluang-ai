from typing import Any

from langgraph.graph import END, StateGraph
from pydantic import BaseModel

from app.shared.logging import get_logger

logger = get_logger("discovery.agent")

MAX_STEPS = 10
MAX_LLM_CALLS = 2
MAX_RUNTIME_S = 90


class DiscoveryState(BaseModel):
    seed_urls: list[str] = []
    search_constraints: dict[str, Any] = {}
    candidates: list[dict[str, Any]] = []
    source_proposals: list[dict[str, Any]] = []
    visited_urls: list[str] = []
    step_count: int = 0
    llm_call_count: int = 0
    current_state: str = "START"
    status: str = "running"
    error: str | None = None


def node_plan_search(state: DiscoveryState) -> DiscoveryState:
    state.step_count += 1
    state.current_state = "PLAN_SEARCH"
    return state


def node_search(state: DiscoveryState) -> DiscoveryState:
    state.step_count += 1
    state.current_state = "SEARCH"
    if state.step_count >= MAX_STEPS:
        state.status = "budget_exhausted"
        state.error = "BUDGET_EXHAUSTED"
    return state


def node_inspect(state: DiscoveryState) -> DiscoveryState:
    state.step_count += 1
    state.current_state = "INSPECT"
    return state


def node_evaluate(state: DiscoveryState) -> DiscoveryState:
    state.step_count += 1
    state.current_state = "EVALUATE"
    return state


def node_register(state: DiscoveryState) -> DiscoveryState:
    state.step_count += 1
    state.current_state = "REGISTER"
    for candidate in state.candidates:
        url = candidate.get("url", "")
        if url and url not in state.visited_urls:
            state.visited_urls.append(url)
    return state


def route_after_search(state: DiscoveryState) -> str:
    if state.status == "budget_exhausted":
        return "end"
    if state.step_count >= MAX_STEPS:
        return "end"
    return "continue"


def build_discovery_graph():
    graph = StateGraph(DiscoveryState)

    graph.add_node("plan_search", node_plan_search)
    graph.add_node("search", node_search)
    graph.add_node("inspect", node_inspect)
    graph.add_node("evaluate", node_evaluate)
    graph.add_node("register", node_register)

    graph.set_entry_point("plan_search")
    graph.add_edge("plan_search", "search")
    graph.add_conditional_edges(
        "search",
        route_after_search,
        {"end": END, "continue": "inspect"},
    )
    graph.add_edge("inspect", "evaluate")
    graph.add_edge("evaluate", "register")
    graph.add_conditional_edges(
        "register",
        lambda s: "end" if s.step_count >= MAX_STEPS else "search",
        {"end": END, "search": "search"},
    )

    return graph.compile()
