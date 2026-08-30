"""Extraction Agent — bounded strategy ladder (Runtime Doc §4 fast-path).

Pure decision logic: DB I/O stays in the calling task. Budget comes from
config/agents.yaml (extraction.max_steps / max_llm_calls).
"""

from enum import Enum

from langgraph.graph import END, StateGraph
from pydantic import BaseModel

from app.modules.ai import get_ai
from app.modules.extraction.deterministic import DEADLINE_KEYWORDS, DeterministicExtractor
from app.modules.extraction.llm_service import LLMExtractionService
from app.modules.extraction.schema import ExtractionSchema
from app.modules.extraction.validation import ValidationService
from app.modules.extraction.vision_service import VisionExtractionService
from app.shared.config import get_agent_budget
from app.shared.logging import get_logger

logger = get_logger("extraction.agent")

MIN_CONFIDENCE = 0.5
OCR_CONFIDENCE_FLOOR = 0.6


class Strategy(str, Enum):
    DETERMINISTIC = "deterministic"
    LLM = "llm"
    VISION = "vision_llm"
    NONE = "none"


class ExtractionState(BaseModel):
    doc_type: str
    text: str = ""
    ocr_confidence: float = 1.0
    image_bytes: bytes | None = None

    det_result: ExtractionSchema | None = None
    final_result: ExtractionSchema | None = None
    confidence: float = 0.0
    strategy_used: Strategy = Strategy.NONE
    llm_calls: int = 0
    steps: int = 0
    status: str = "running"
    error: str | None = None

    @property
    def max_llm_calls(self) -> int:
        return int(get_agent_budget("extraction").get("max_llm_calls", 2))

    @property
    def max_steps(self) -> int:
        return int(get_agent_budget("extraction").get("max_steps", 8))


def _conf_of(result: ExtractionSchema | None) -> float:
    if result is None:
        return 0.0
    return ValidationService().compute_overall_confidence(result)


def _det_to_schema(det) -> ExtractionSchema | None:
    """Convert DeterministicExtractor's DeterministicResult to ExtractionSchema."""
    if det is None:
        return None
    return ExtractionSchema(
        title=det.title,
        description=det.description,
        end_date=det.end_date.isoformat() if det.end_date else None,
        start_date=det.start_date.isoformat() if det.start_date else None,
        organizer=det.organizer,
        location=det.location,
        prize=det.prize,
        category=det.category,
        gpa_requirement=det.gpa_requirement,
        field_confidence={"overall": det.confidence},
    )


async def node_detect(state: ExtractionState) -> ExtractionState:
    state.steps += 1
    logger.info(
        "ex_agent_detect",
        doc_type=state.doc_type,
        text_len=len(state.text),
        has_image=state.image_bytes is not None,
    )
    return state


def _has_any_date(text: str) -> bool:
    """Pre-screen (Runtime §12): tanpa pola tanggal apa pun -> jangan buang resource LLM."""
    import re

    patterns = [
        r"\d{1,2}\s+(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)",
        r"\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}",
        r"\d{4}[-/]\d{1,2}[-/]\d{1,2}",
    ]
    return any(re.search(p, text, re.I) for p in patterns)


async def node_try_deterministic(state: ExtractionState) -> ExtractionState:
    state.steps += 1
    if not state.text or len(state.text.strip()) < 40:
        state.status = "needs_llm"
        return state

    # P0: dokumen tanpa jejak tanggal sama sekali -> terminal, hemat LLM (Runtime §12)
    if not _has_any_date(state.text):
        state.status = "failed"
        state.error = "NO_CONTENT_FOUND"
        state.strategy_used = Strategy.DETERMINISTIC
        state.det_result = _det_to_schema(DeterministicExtractor().extract_text(state.text)) if len(state.text) >= 100 else None
        logger.info("ex_agent_prescreen_skip", text_len=len(state.text))
        return state

    det = DeterministicExtractor()
    result = det.extract_text(state.text)
    converted = _det_to_schema(result)
    state.det_result = converted
    confidence = _conf_of(converted)

    ok, reason = ValidationService().validate(converted)
    date_ok = ok or reason == "end_date_in_past"

    if confidence >= MIN_CONFIDENCE and date_ok:
        state.final_result = converted
        state.confidence = confidence
        state.strategy_used = Strategy.DETERMINISTIC
        state.status = "valid"
        logger.info("ex_agent_fastpath_hit", confidence=confidence)
    else:
        # Kurang meyakinkan / tidak ada deadline → serahkan ke LLM
        state.status = "needs_llm"
    return state


async def node_try_llm(state: ExtractionState) -> ExtractionState:
    state.steps += 1
    if state.status == "valid":
        return state
    if not state.text or len(state.text.strip()) < 20:
        state.status = "failed"
        state.error = "NO_CONTENT_FOUND"
        return state
    if state.llm_calls >= state.max_llm_calls or state.steps >= state.max_steps:
        state.status = "budget_exhausted"
        state.error = "BUDGET_EXHAUSTED"
        # fallback ke hasil deterministic low-confidence bila ada
        if state.det_result is not None:
            state.final_result = state.det_result
            state.confidence = _conf_of(state.det_result)
            state.strategy_used = Strategy.DETERMINISTIC
        return state

    state.llm_calls += 1

    # P1 (Runtime §3): prompt ringkas — hanya cari field yang deterministic lewatkan
    import json
    import re

    from app.modules.extraction.schema import EXTRACTION_PROMPT_TEMPLATE

    if state.det_result is not None and (state.det_result.title or state.det_result.category):
        lines = [
            ln
            for ln in state.text.split(". ")
            if any(re.search(k, ln, re.I) for k in DEADLINE_KEYWORDS)
            or re.search(r"\d{1,2}\s+\w+\s+\d{4}|\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}", ln)
        ]
        snippet = " ".join(lines)[:800] if lines else state.text[:600]
        det_dict = state.det_result.to_dict()
        prompt = (
            "Konteks hasil ekstraksi parser (field kosong perlu dilengkapi):\n"
            f"{json.dumps(det_dict, ensure_ascii=False, default=str)}\n\n"
            "Cari DEADLINE peluang dari cuplikan teks berikut. "
            'Jawab HANYA JSON: {"end_date": "YYYY-MM-DD" atau null, '
            '"organizer": "string atau null", "location": "string atau null"}\n\n'
            f"Teks:\n{snippet}"
        )
        max_tok = 400
    else:
        prompt = EXTRACTION_PROMPT_TEMPLATE.format(text=state.text[:2000])
        max_tok = 1200

    llm = LLMExtractionService(get_ai())
    result = await llm.extract_single(prompt, max_tokens=max_tok, raw_prompt=True)

    if result:
        # P1: hasil LLM hanya melengkapi field kosong dari deterministic
        if state.det_result is not None:
            base = state.det_result.model_dump()
            for k, v in result.to_dict().items():
                if k == "field_confidence":
                    continue
                if base.get(k) in (None, "") and v not in (None, ""):
                    base[k] = v
            merged = ExtractionSchema(**base)
            state.final_result = merged
            state.confidence = _conf_of(merged)
            state.strategy_used = Strategy.LLM
        else:
            state.final_result = result
            state.confidence = _conf_of(result)
            state.strategy_used = Strategy.LLM
        state.status = "valid"
    elif state.det_result is not None:
        state.final_result = state.det_result
        state.confidence = _conf_of(state.det_result)
        state.strategy_used = Strategy.DETERMINISTIC
        state.status = "valid"
    else:
        state.status = "llm_failed"
        state.error = "PROVIDER_ERROR"
    return state


async def node_try_vision(state: ExtractionState) -> ExtractionState:
    state.steps += 1
    if (
        state.doc_type != "IMAGE"
        or state.image_bytes is None
        or state.llm_calls >= state.max_llm_calls
        or state.steps >= state.max_steps
    ):
        return state
    if state.ocr_confidence >= OCR_CONFIDENCE_FLOOR and state.text:
        return state

    state.llm_calls += 1
    vision = VisionExtractionService(get_ai())
    result = await vision.extract_from_image(state.image_bytes)

    if result:
        validation = ValidationService()
        state.final_result = result
        state.confidence = validation.compute_overall_confidence(result)
        state.strategy_used = Strategy.VISION
        state.status = "valid"
    elif state.det_result is not None:
        state.final_result = state.det_result
        state.confidence = _conf_of(state.det_result)
        state.strategy_used = Strategy.DETERMINISTIC
        state.status = "valid"
    else:
        state.status = "failed"
        state.error = "VISION_FAILED"
    return state


def route_after_deterministic(state: ExtractionState) -> str:
    if state.status == "valid":
        return "finalize"
    if state.doc_type == "IMAGE" and state.image_bytes is not None and len(state.text.strip()) < 40:
        return "try_vision"
    return "try_llm"


def route_after_llm(state: ExtractionState) -> str:
    if state.status == "valid":
        return "finalize"
    if state.doc_type == "IMAGE" and state.image_bytes is not None and state.llm_calls < state.max_llm_calls:
        return "try_vision"
    return "finalize"


async def node_finalize(state: ExtractionState) -> ExtractionState:
    state.steps += 1
    validation = ValidationService()

    if state.final_result is None:
        if state.status == "running":
            state.error = "NO_STRATEGY_SUCCEEDED"
        state.status = "failed"
    else:
        ok, reason = validation.validate(state.final_result)
        date_ok = ok or reason == "end_date_in_past"
        conf_ok = state.confidence >= MIN_CONFIDENCE

        if date_ok and conf_ok:
            # Ekstraksi berhasil; peluang kadaluarsa tetap disimpan dan
            # difilter oleh candidate pipeline + lifecycle cron.
            state.status = "valid"
        elif date_ok:
            state.status = "needs_recovery"
        else:
            state.status = "invalid"
    logger.info(
        "ex_agent_done",
        strategy=state.strategy_used.value,
        confidence=state.confidence,
        status=state.status,
        llm_calls=state.llm_calls,
        steps=state.steps,
    )
    return state


def build_extraction_graph():
    graph = StateGraph(ExtractionState)

    graph.add_node("detect", node_detect)
    graph.add_node("try_deterministic", node_try_deterministic)
    graph.add_node("try_llm", node_try_llm)
    graph.add_node("try_vision", node_try_vision)
    graph.add_node("finalize", node_finalize)

    graph.set_entry_point("detect")
    graph.add_edge("detect", "try_deterministic")
    graph.add_conditional_edges(
        "try_deterministic",
        route_after_deterministic,
        {"finalize": "finalize", "try_llm": "try_llm", "try_vision": "try_vision"},
    )
    graph.add_conditional_edges(
        "try_llm",
        route_after_llm,
        {"finalize": "finalize", "try_vision": "try_vision"},
    )
    graph.add_edge("try_vision", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile()


extraction_graph = build_extraction_graph()
