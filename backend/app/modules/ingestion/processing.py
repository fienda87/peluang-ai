"""Document processing: load → Extraction Agent graph → persist → upsert → dedup → embed."""

import json
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure import get_storage
from app.modules.ai import get_ai
from app.modules.deduplication.service import DeduplicationService
from app.modules.embedding.service import EmbeddingService
from app.shared.logging import get_logger

logger = get_logger("ingestion.processing")


async def process_document(
    session: AsyncSession,
    doc_uuid: uuid.UUID,
    redis=None,
) -> dict:
    from app.agents.extraction.graph import ExtractionState, extraction_graph

    result = await session.execute(
        text("SELECT doc_type, extracted_text, ocr_used FROM raw_documents WHERE id = :id"),
        {"id": doc_uuid},
    )
    row = result.one_or_none()
    if not row:
        logger.error("document_not_found", doc_id=str(doc_uuid))
        return {"status": "error", "reason": "document_not_found"}

    doc_type, extracted_text, _ocr_used = row

    image_bytes = None
    ocr_confidence = 1.0
    if doc_type == "IMAGE":
        from app.modules.ingestion.ocr_adapter import OCRAdapter

        doc_meta = await session.execute(
            text("SELECT file_url FROM raw_documents WHERE id = :id"),
            {"id": doc_uuid},
        )
        file_url = doc_meta.scalar()
        if file_url and file_url.startswith("local://"):
            try:
                image_bytes = await get_storage().get(file_url.removeprefix("local://"))
            except Exception as e:
                logger.error("image_load_failed", doc_id=str(doc_uuid), error=str(e))
        if image_bytes and not extracted_text:
            ocr = OCRAdapter()
            ocr_result = ocr.extract(image_bytes)
            extracted_text = ocr_result.text
            ocr_confidence = ocr_result.confidence
    elif not extracted_text and doc_type in ("HTML", "PDF"):
        from app.modules.extraction.deterministic import strip_html

        doc_meta = await session.execute(
            text("SELECT file_url FROM raw_documents WHERE id = :id"),
            {"id": doc_uuid},
        )
        file_url = doc_meta.scalar()
        raw_bytes = b""
        if file_url and file_url.startswith("local://"):
            try:
                raw_bytes = await get_storage().get(file_url.removeprefix("local://"))
            except Exception as e:
                logger.error("file_load_failed", doc_id=str(doc_uuid), error=str(e))
        if doc_type == "HTML":
            extracted_text = strip_html(raw_bytes.decode("utf-8", errors="ignore"))
        else:
            from app.modules.ingestion.pdf_adapter import PDFAdapter

            pdf_result = PDFAdapter().extract_text(raw_bytes)
            extracted_text = pdf_result.text

    # --- Extraction Agent (LangGraph) ---

    state = ExtractionState(
        doc_type=doc_type or "HTML",
        text=extracted_text or "",
        ocr_confidence=ocr_confidence,
        image_bytes=image_bytes,
    )
    graph_result = await extraction_graph.ainvoke(state)
    final_state = (
        graph_result if isinstance(graph_result, ExtractionState) else ExtractionState(**graph_result)
    )

    _DB_STATUS = {
        "valid": "success",
        "budget_exhausted": "budget_exhausted",
    }
    db_status = _DB_STATUS.get(final_state.status, "failed")

    _STRATEGY_DB = {
        "deterministic": "regex",
        "llm": "llm",
        "vision_llm": "vision_llm",
        "none": "manual",
    }
    strategy_db = _STRATEGY_DB.get(final_state.strategy_used.value, "regex")

    agent_run_id = uuid.uuid4()
    await session.execute(
        text(
            "INSERT INTO agent_runs (id, agent_type, status, step_count, llm_call_count, "
            "failure_code, output_summary, started_at, ended_at, duration_ms) "
            "VALUES (:id, 'extraction', :status, :steps, :llm_calls, :failure, CAST(:summary AS jsonb), "
            "now(), now(), 0)"
        ),
        {
                "id": agent_run_id,
                "status": db_status,
            "steps": final_state.steps,
            "llm_calls": final_state.llm_calls,
            "failure": final_state.error,
            "summary": json.dumps({
                "strategy": final_state.strategy_used.value,
                "confidence": float(final_state.confidence),
                "doc": str(doc_uuid),
            }),
        },
    )

    strategy = final_state.strategy_used.value
    if final_state.final_result is None:
        await session.execute(
            text(
            "INSERT INTO extraction_results (id, raw_document_id, strategy, extracted_data, "
            "overall_confidence, status, version) VALUES (:id, :doc_id, :strategy, CAST(:data AS jsonb), "
            "0, 'failed', 1)"
            ),
            {"id": uuid.uuid4(), "doc_id": doc_uuid, "strategy": strategy},
        )
        await session.commit()
        logger.warning("extract_failed", doc_id=str(doc_uuid), error=final_state.error)
        return {
            "status": "error",
            "reason": final_state.error or "extraction_failed",
            "agent_run_id": str(agent_run_id),
        }

    data = final_state.final_result.to_dict()
    if data.get("title"):
        from app.modules.extraction.deterministic import clean_title

        data["title"] = clean_title(str(data["title"]))
    extraction_id = uuid.uuid4()
    await session.execute(
        text(
            "INSERT INTO extraction_results (id, raw_document_id, strategy, extracted_data, "
            "overall_confidence, status, version) VALUES (:id, :doc_id, :strategy, CAST(:data AS jsonb), "
            ":conf, :status, 1)"
        ),
        {
            "id": extraction_id,
            "doc_id": doc_uuid,
            "strategy": strategy_db,
            "data": json.dumps(data),
            "conf": float(final_state.confidence),
            "status": final_state.status,
        },
    )

    # --- Persist opportunity bila valid ---
    opportunity_id = None
    if final_state.status == "valid" and data.get("title") and data.get("category"):
        from datetime import date as date_cls

        from app.modules.opportunities.service import OpportunitiesService

        opp_svc = OpportunitiesService(session)
        end_date = None
        if data.get("end_date"):
            try:
                end_date = date_cls.fromisoformat(str(data["end_date"])[:10])
            except ValueError:
                end_date = None

        source_row = await session.execute(
            text("SELECT source_id FROM raw_documents WHERE id = :id"),
            {"id": doc_uuid},
        )
        src_id = source_row.scalar()

        meta_row = await session.execute(
            text("SELECT meta ->> 'source_page' FROM raw_documents WHERE id = :id"),
            {"id": doc_uuid},
        )
        source_page = meta_row.scalar()
        if not source_page:
            src_url_row = await session.execute(
                text("SELECT source_url FROM sources WHERE id = :sid"),
                {"sid": src_id},
            )
            source_page = src_url_row.scalar()

        opportunity_id = await opp_svc.upsert_opportunity(
            source_id=src_id,
            title=data["title"],
            category=data["category"],
            end_date=end_date,
            organizer=data.get("organizer"),
            location=data.get("location"),
            description=(data.get("description") or "")[:2000] or None,
            prize=data.get("prize"),
            url=source_page,
        )

        from app.shared.eventbus import publish

        publish(
            "opp.created",
            f"✨ PELUANG BARU [{data['category']}] {data['title'][:80]}"
            + (f" — deadline {end_date}" if end_date else ""),
            level="success",
            title=data["title"],
            category=data["category"],
        )

        await session.execute(
            text("UPDATE raw_documents SET opportunity_id = :oid WHERE id = :did"),
            {"oid": opportunity_id, "did": doc_uuid},
        )

        if data.get("gpa_requirement"):
            await opp_svc.add_requirements(
                opportunity_id,
                {"gpa": f"IPK minimal {data['gpa_requirement']}"},
            )

        # Dedup: via redis (worker) atau inline (CLI)
        if redis:
            await redis.enqueue_job("deduplicate_opportunity_task", str(opportunity_id))
        else:
            try:
                dedup_svc = DeduplicationService(session)
                dup_result = await session.execute(
                    text("SELECT title, url, end_date FROM opportunities WHERE id = :id"),
                    {"id": opportunity_id},
                )
                t, u, d = dup_result.one()
                dups = await dedup_svc.find_duplicates(
                    str(opportunity_id), t, u, str(d) if d else None
                )
                if dups:
                    dup_id, method, score = dups[0]
                    await dedup_svc.resolve_duplicate(
                        str(opportunity_id), dup_id, method, score
                    )
                    publish(
                        "dedup.resolved",
                        f"♻️ Duplikat dilewati ({method}, skor {score})",
                    )
                else:
                    await dedup_svc.mark_canonical(str(opportunity_id))
            except Exception as e:
                logger.warning("dedup_inline_failed", error=str(e))

        # Embedding best-effort
        try:
            await EmbeddingService(session, get_ai()).embed_opportunities([opportunity_id])
        except Exception as e:
            logger.warning("embed_skipped", opp=str(opportunity_id), error=str(e))

    await session.commit()

    from app.shared.eventbus import publish

    icon = {"valid": "⚡", "needs_recovery": "🛠"}.get(
        final_state.status, "⚙️"
    )
    publish(
        "extract.strategy",
        f"{icon} Ekstraksi {strategy_db} · conf {final_state.confidence:.2f} · "
        f"LLM {final_state.llm_call_count}x",
        level="success" if final_state.status == "valid" else "warn",
    )

    logger.info(
        "process_document_done",
        doc_id=str(doc_uuid),
        status=final_state.status,
        confidence=float(final_state.confidence),
        llm_calls=final_state.llm_calls,
        opportunity=str(opportunity_id) if opportunity_id else None,
    )
    return {
        "status": "ok",
        "extraction_status": final_state.status,
        "confidence": float(final_state.confidence),
        "llm_calls": final_state.llm_calls,
        "strategy": strategy_db,
        "opportunity_id": str(opportunity_id) if opportunity_id else None,
        "agent_run_id": str(agent_run_id),
    }
