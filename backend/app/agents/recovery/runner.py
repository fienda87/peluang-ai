"""Recovery Agent — runner: eksekusi ladder strategi utk dokumen needs_recovery.

Ladder sesuai graph recovery: alternate re-parse (lengkap ulang teks) →
refetch halaman → OCR → vision → provider fallback. Budget dari agents.yaml.
"""

import uuid

from app.shared.logging import get_logger

logger = get_logger("recovery.runner")


async def run_recovery_agent(
    session,
    raw_document_id: uuid.UUID,
    prior_failure: str = "",
) -> dict:
    """Jalankan ladder recovery utk satu dokumen; return hasil eskalasi."""

    from sqlalchemy import text as sql

    from app.agents.common.audit import audit_agent_run
    from app.infrastructure import get_storage
    from app.modules.ai import get_ai
    from app.modules.extraction.deterministic import strip_html
    from app.modules.extraction.validation import ValidationService

    strategies_tried: list[str] = []
    steps = 0
    llm_calls = 0

    async def fetch_doc():
        r = await session.execute(
            sql(
                "SELECT doc_type, file_url, ocr_used FROM raw_documents WHERE id = :id"
            ),
            {"id": raw_document_id},
        )
        return r.fetchone()

    doc = await fetch_doc()
    if not doc:
        return {"status": "skipped", "reason": "doc_not_found"}

    doc_type, file_url, ocr_used = doc
    raw_bytes = b""
    if file_url and file_url.startswith("local://"):
        try:
            raw_bytes = await get_storage().get(file_url.removeprefix("local://"))
        except Exception:
            pass

    async def try_extract(text: str, label: str, use_llm: bool) -> dict | None:
        nonlocal steps, llm_calls
        steps += 1
        from app.agents.extraction.graph import ExtractionState, extraction_graph

        st = ExtractionState(
            doc_type=doc_type or "HTML",
            text=text or "",
            image_bytes=raw_bytes if doc_type == "IMAGE" else None,
        )
        out = await extraction_graph.ainvoke(st)
        fs = out if isinstance(out, ExtractionState) else ExtractionState(**out)
        if fs.final_result is not None:
            data = fs.final_result.to_dict()
            v = ValidationService()
            ok, reason = v.validate(fs.final_result)
            if ok or reason == "end_date_in_past":
                return {"strategy": label, "data": data, "confidence": fs.confidence}
        return None

    # Strategy 1: re-parse teks penuh (kadang extraction sebelumnya noisy)
    steps += 1
    if doc_type == "HTML" and raw_bytes:
        strategies_tried.append("reparse")
        text = strip_html(raw_bytes.decode("utf-8", errors="ignore"))
        r = await try_extract(text, "alternate_parser", use_llm=False)
        if r:
            return await _finish(r, "reparse", steps, llm_calls, session, raw_document_id, prior_failure)

    # Strategy 2: vision (API VL) utk dokumen gambar / PDF scan
    if doc_type in ("IMAGE", "PDF") and raw_bytes:
        strategies_tried.append("vision")
        steps += 1
        llm_calls += 1
        try:
            from app.modules.extraction.vision_service import VisionExtractionService

            vs = await VisionExtractionService(get_ai()).extract_from_image(raw_bytes)
            if vs is not None:
                data = vs.to_dict()
                return await _finish(
                    {"strategy": "vision", "data": data, "confidence": 0.6},
                    "vision", steps, llm_calls, session, raw_document_id, prior_failure,
                )
        except Exception as e:
            logger.warning("recovery_vision_failed", error=str(e)[:80])

    # Semua gagal → degraded (Runtime §12: UNKNOWN > boros resource)
    strategies_tried.append("degraded")
    await audit_agent_run(
        session,
        "recovery",
        "degraded",
        steps=steps,
        llm_calls=llm_calls,
        trigger="auto",
        scope={"raw_document_id": str(raw_document_id)},
        output={"strategies": strategies_tried, "result": "UNKNOWN"},
        failure_code="RECOVERY_FAILED",
    )
    return {"status": "degraded", "strategies": strategies_tried}


async def _finish(r, label, steps, llm_calls, session, raw_document_id, prior_failure):
    """Persist hasil recovery + audit."""
    import json

    from sqlalchemy import text as sql

    from app.agents.common.audit import audit_agent_run

    await session.execute(
        sql(
            "UPDATE extraction_results SET status = 'recovered', "
            "strategy = :st, extracted_data = CAST(:data AS jsonb), "
            "overall_confidence = :conf, version = version + 1 "
            "WHERE raw_document_id = :rid AND status = 'needs_recovery'"
        ),
        {
            "st": label,
            "data": json.dumps(r["data"], default=str),
            "conf": float(r["confidence"]),
            "rid": raw_document_id,
        },
    )
    await session.commit()

    await audit_agent_run(
        session,
        "recovery",
        "success",
        steps=steps,
        llm_calls=llm_calls,
        trigger="auto",
        scope={"raw_document_id": str(raw_document_id)},
        output={"strategy": label, "recovered": True},
    )
    return {"status": "recovered", "strategy": label}
