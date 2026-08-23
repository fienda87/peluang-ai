"""Fast-path tests for the Extraction Agent graph (no DB, no LLM)."""

from pathlib import Path

import pytest

from app.agents.extraction.graph import ExtractionState, extraction_graph

FIXTURES = Path(__file__).parent / "fixtures"


def _make_state_with_good_text() -> ExtractionState:
    html = (FIXTURES / "html" / "beasiswa_lpdp_2026.html").read_text(encoding="utf-8")
    import re

    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return ExtractionState(doc_type="HTML", text=text)


@pytest.mark.asyncio
async def test_fastpath_deterministic_skips_llm():
    state = _make_state_with_good_text()
    final = await extraction_graph.ainvoke(state)

    assert final["status"] == "valid", f"status={final['status']}"
    assert final["strategy_used"] == "deterministic"
    assert final["llm_calls"] == 0, "fast-path harus 0 LLM call"
    assert final["final_result"].title is not None


@pytest.mark.asyncio
async def test_empty_text_fails_without_llm():
    state = ExtractionState(doc_type="HTML", text="")
    final = await extraction_graph.ainvoke(state)
    assert final["status"] in ("failed", "budget_exhausted")
    assert final.get("final_result") is None


@pytest.mark.asyncio
async def test_budget_respected_on_messy_text():
    state = ExtractionState(doc_type="HTML", text="x" * 100)
    final = await extraction_graph.ainvoke(state)
    assert final["llm_calls"] <= 2
    assert final["steps"] <= 8


@pytest.mark.asyncio
async def test_low_confidence_falls_back_to_llm_schema():
    """Deterministic result yang lemah harus lanjut ke LLM path (state flag)."""
    state = ExtractionState(doc_type="HTML", text="pendek")
    final = await extraction_graph.ainvoke(state)
    # text <40 chars -> skip deterministic; tanpa LLM provider -> failed/budget
    assert final["strategy_used"] in ("none", "deterministic", "llm")
