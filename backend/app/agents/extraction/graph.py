from enum import Enum
from typing import Any

from langgraph.graph import END, StateGraph
from pydantic import BaseModel

from app.modules.ai import get_ai
from app.modules.extraction.deterministic import DeterministicExtractor
from app.modules.extraction.llm_service import LLMExtractionService
from app.modules.extraction.validation import ValidationService
from app.modules.extraction.vision_service import VisionExtractionService
from app.shared.logging import get_logger

logger = get_logger("extraction.agent")


class ExtractionState(BaseModel):
    raw_document_id: str
    doc_type: str
    extracted_text: str | None = None
    image_bytes: bytes | None = None
    step_count: int = 0
    llm_call_count: int = 0
    current_state: str = "START"
    extracted_data: dict[str, Any] | None = None
    confidence: float = 0.0
    error: str | None = None
    status: str = "running"


class ExtractionStrategy(str, Enum):
    DETERMINISTIC = "deterministic"
    LLM = "llm"
    VISION = "vision"
    FAILED = "failed"


def node_load(state: ExtractionState) -> ExtractionState:
    state.step_count += 1
    state.current_state = "LOAD"
    logger.info("extraction_load", step=state.step_count)
    return state


def node_detect_type(state: ExtractionState) -> ExtractionState:
    state.step_count += 1
    state.current_state = "DETECT_TYPE"
    return state


async def node_extract_deterministic(state: ExtractionState) -> ExtractionState:
    if not state.extracted_text:
        state.error = "no_text"
        return state

    state.step_count += 1
    det = DeterministicExtractor()
    result = det.extract_text(state.extracted_text)

    validation = ValidationService()
    confidence = validation.compute_overall_confidence(result)

    if confidence >= 0.5:
        state.extracted_data = result.to_dict()
        state.confidence = confidence
        state.status = "valid"
        state.current_state = "END"
        return state

    state.current_state = "EXTRACT_LLM"
    return state


async def node_extract_llm(state: ExtractionState) -> ExtractionState:
    if state.llm_call_count >= 2:
        state.error = "llm_budget_exhausted"
        state.status = "budget_exhausted"
        return state

    state.step_count += 1
    state.llm_call_count += 1

    llm_svc = LLMExtractionService(get_ai())
    result = await llm_svc.extract_single(state.extracted_text or "")

    if result:
        validation = ValidationService()
        confidence = validation.compute_overall_confidence(result)
        state.extracted_data = result.to_dict()
        state.confidence = confidence
        state.status = "valid"
        state.current_state = "END"
    else:
        state.current_state = "EXTRACT_VISION"

    return state


async def node_extract_vision(state: ExtractionState) -> ExtractionState:
    if not state.image_bytes:
        state.error = "no_image"
        state.status = "failed"
        state.current_state = "END"
        return state

    if state.llm_call_count >= 2:
        state.error = "llm_budget_exhausted"
        state.status = "budget_exhausted"
        state.current_state = "END"
        return state

    state.step_count += 1
    state.llm_call_count += 1

    vision_svc = VisionExtractionService(get_ai())
    result = await vision_svc.extract_from_image(state.image_bytes)

    if result:
        validation = ValidationService()
        confidence = validation.compute_overall_confidence(result)
        state.extracted_data = result.to_dict()
        state.confidence = confidence
        state.status = "recovered"
        state.current_state = "END"
    else:
        state.error = "vision_failed"
        state.status = "failed"
        state.current_state = "END"

    return state


def build_extraction_graph():
    graph = StateGraph(ExtractionState)

    graph.add_node("load", node_load)
    graph.add_node("detect_type", node_detect_type)
    graph.add_node("extract_deterministic", node_extract_deterministic)
    graph.add_node("extract_llm", node_extract_llm)
    graph.add_node("extract_vision", node_extract_vision)

    graph.set_entry_point("load")

    graph.add_edge("load", "detect_type")
    graph.add_edge("detect_type", "extract_deterministic")
    graph.add_conditional_edges(
        "extract_deterministic",
        lambda s: "END" if s.status == "valid" else "extract_llm",
        {"END": END, "extract_llm": "extract_llm"},
    )
    graph.add_conditional_edges(
        "extract_llm",
        lambda s: "END" if s.status in ("valid", "budget_exhausted", "failed") else "extract_vision",
        {"END": END, "extract_vision": "extract_vision"},
    )
    graph.add_edge("extract_vision", END)

    return graph.compile()
