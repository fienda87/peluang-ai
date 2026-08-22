from typing import Any

from langgraph.graph import END, StateGraph
from pydantic import BaseModel

from app.shared.logging import get_logger

logger = get_logger("recovery.agent")

MAX_ATTEMPTS = 2
MAX_STEPS = 8
MAX_LLM_CALLS = 3
SAME_STRATEGY_RETRY = 1


class RecoveryState(BaseModel):
    extraction_result_id: str
    failure_reason: str = ""
    prior_strategies: list[str] = []
    selected_strategy: str | None = None
    attempts: int = 0
    step_count: int = 0
    llm_call_count: int = 0
    current_state: str = "START"
    status: str = "running"
    result: dict[str, Any] | None = None
    error: str | None = None


STRATEGY_LADDER = ["alternate_parser", "refetch", "ocr", "vision_llm", "provider_fallback"]


def node_diagnose(state: RecoveryState) -> RecoveryState:
    state.step_count += 1
    state.current_state = "DIAGNOSE"
    logger.info("recovery_diagnose", reason=state.failure_reason)
    return state


def node_select_strategy(state: RecoveryState) -> RecoveryState:
    state.step_count += 1
    state.current_state = "SELECT_STRATEGY"

    if state.attempts >= MAX_ATTEMPTS:
        state.status = "degraded"
        state.error = "BUDGET_EXHAUSTED"
        return state

    for strategy in STRATEGY_LADDER:
        used_count = state.prior_strategies.count(strategy)
        if used_count < SAME_STRATEGY_RETRY:
            state.selected_strategy = strategy
            state.prior_strategies.append(strategy)
            return state

    state.status = "degraded"
    state.error = "NO_STRATEGY_AVAILABLE"
    return state


def node_execute(state: RecoveryState) -> RecoveryState:
    state.step_count += 1
    state.current_state = "EXECUTE"
    state.attempts += 1

    if state.selected_strategy in ("vision_llm", "provider_fallback"):
        state.llm_call_count += 1
        if state.llm_call_count > MAX_LLM_CALLS:
            state.status = "budget_exhausted"
            state.error = "BUDGET_EXHAUSTED"
            return state

    return state


def node_validate(state: RecoveryState) -> RecoveryState:
    state.step_count += 1
    state.current_state = "VALIDATE"

    if state.status in ("degraded", "budget_exhausted"):
        return state

    if state.result is not None:
        state.status = "success"
    elif state.attempts < MAX_ATTEMPTS and state.step_count < MAX_STEPS:
        state.current_state = "SELECT_STRATEGY"
    else:
        state.status = "degraded"
        state.error = "RECOVERY_FAILED"

    return state


def route_after_validate(state: RecoveryState) -> str:
    if state.status == "success":
        return "end"
    if state.current_state == "SELECT_STRATEGY":
        return "retry"
    return "end"


def build_recovery_graph():
    graph = StateGraph(RecoveryState)

    graph.add_node("diagnose", node_diagnose)
    graph.add_node("select_strategy", node_select_strategy)
    graph.add_node("execute", node_execute)
    graph.add_node("validate", node_validate)

    graph.set_entry_point("diagnose")
    graph.add_edge("diagnose", "select_strategy")
    graph.add_conditional_edges(
        "select_strategy",
        lambda s: "end" if s.status in ("degraded", "budget_exhausted") else "execute",
        {"end": END, "execute": "execute"},
    )
    graph.add_edge("execute", "validate")
    graph.add_conditional_edges(
        "validate",
        route_after_validate,
        {"end": END, "retry": "select_strategy"},
    )

    return graph.compile()
