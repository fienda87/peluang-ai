"""Smoke test semua tool ingestion: PASS/FAIL per komponen."""
import asyncio

RESULT: list[tuple[str, bool, str]] = []


def record(name: str, ok: bool, note: str = ""):
    RESULT.append((name, ok, note))
    print(f"{'PASS' if ok else 'FAIL'} | {name}" + (f" | {note}" if note else ""))


async def main():
    # 1. HTML fetcher (httpx)
    from app.modules.ingestion.html_adapter import HTMLFetcher

    f = HTMLFetcher()
    r = await f.fetch("https://djarumbeasiswaplus.org/")
    record("1. HTTP fetcher", r.success and len(r.content) > 1000,
           f"{len(r.content)} bytes")

    # 2. Link extraction + filter
    links = f.extract_links(r.content.decode("utf-8", errors="ignore"), r.url)
    from app.modules.ingestion.pipeline import CrawlPipeline
    pipe = CrawlPipeline.__new__(CrawlPipeline)  # tanpa DB utk test filter
    pipe.fetcher = f
    filtered = pipe._filter_links(links, r.url)
    record("2. Extract+filter links", len(links) > 0 and len(filtered) > 0,
           f"total={len(links)} lolos={len(filtered)}")

    # 3. Crawl4AI escalation (import + optional run)
    try:
        import crawl4ai  # noqa: F401

        has_c4 = True
    except ImportError:
        has_c4 = False
    if has_c4:
        res = await pipe._fetch_smart("https://example.com")
        record("3. Crawl4AI escalation", res.success, f"status={res.status_code}")
    else:
        record("3. Crawl4AI escalation", False, "paket tidak terpasang")

    # 4. RSS adapter
    from app.modules.ingestion.rss_api_adapter import RSSAdapter

    rss_urls = [
        "https://beasiswaindo.com/feed/",
        "https://djarumbeasiswaplus.org/feed/",
    ]
    items = []
    for u in rss_urls:
        try:
            items = await RSSAdapter().fetch_feed(u)
            if items:
                break
        except Exception:
            continue
    record("4. RSS adapter", len(items) > 0, f"{len(items)} items")

    # 5. Document detection
    from app.modules.ingestion.detect import detect_doc_type

    ok = (
        detect_doc_type(b"<html><body>x</body></html>", "") == "HTML"
        and detect_doc_type(b"%PDF-1.7 fake", "application/pdf") == "PDF"
        and detect_doc_type(b"\x89PNG\r\n\x1a\nxxxx", "image/png") == "IMAGE"
    )
    record("5. Doc type detection", ok)

    # 6. PDF adapter (fixture)
    from pathlib import Path

    from app.modules.ingestion.pdf_adapter import PDFAdapter

    pdf_files = list(Path("tests/fixtures/pdf").glob("*.pdf"))
    pr = PDFAdapter().extract_text(pdf_files[0].read_bytes())
    record("6. PDF parser", pr.page_count >= 1, f"pages={pr.page_count} text={len(pr.text)}")

    # 7. Deterministic extractor (fixture HTML)
    from app.modules.extraction.deterministic import DeterministicExtractor

    html = Path("tests/fixtures/html/beasiswa_lpdp_2026.html").read_text(encoding="utf-8")
    det = DeterministicExtractor().extract_html(html)
    record("7. Deterministic extractor",
           det.title is not None and det.category == "beasiswa",
           f"cat={det.category} conf={det.confidence}")

    # 8. OCR (Tesseract lokal)
    try:
        from app.modules.ingestion.ocr_adapter import OCRAdapter

        img = Path("tests/fixtures/image/poster_beasiswa_chevening.png").read_bytes()
        ocr = OCRAdapter().extract(img)
        record("8. OCR Tesseract", len(ocr.text) > 20,
               f"conf={ocr.confidence:.2f} chars={len(ocr.text)}")
    except Exception as e:
        record("8. OCR Tesseract", False, str(e)[:80])

    # 9. Local embedding (MiniLM)
    try:
        from app.modules.embedding.service import embed_texts_local

        vecs = embed_texts_local(["beasiswa S2 luar negeri", "magang startup"])
        record("9. Local embedding MiniLM",
               len(vecs) == 2 and len(vecs[0]) == 384,
               f"dims={len(vecs[0])}")
    except Exception as e:
        record("9. Local embedding MiniLM", False, str(e)[:80])

    # 10. LLM chat via OpenRouter + fallback chain
    from app.modules.ai import get_ai

    try:
        resp = await get_ai().chat(
            messages=[{"role": "user", "content": "Reply one word: ready"}],
            max_tokens=2000,
        )
        record("10. LLM chat (fallback chain)", len(resp.content) > 0,
               f"model={resp.model[:40]}")
    except Exception as e:
        record("10. LLM chat (fallback chain)", False, str(e)[:80])

    # 11. Vision path (fixture poster -> Vision LLM)
    try:
        from app.modules.extraction.vision_service import VisionExtractionService

        img2 = Path("tests/fixtures/image/poster_lomba_foto.png").read_bytes()
        vs = await VisionExtractionService(get_ai()).extract_from_image(img2)
        record("11. Vision extraction", vs is not None and vs.title is not None,
               f"title={(vs.title or '')[:40] if vs else '-'}")
    except Exception as e:
        record("11. Vision extraction", False, str(e)[:80])

    # 12. Full mini pipeline: crawl 1 source asli
    from sqlalchemy import text as sqltext

    from app.infrastructure import get_storage
    from app.infrastructure.database import async_session_factory

    async with async_session_factory() as session:
        sid = await session.execute(
            sqltext(
                "SELECT id FROM sources WHERE is_active = TRUE AND access_method='http' "
                "LIMIT 1"
            )
        )
        source_id = sid.scalar()
        pipeline = CrawlPipeline(session, get_storage())
        cres = await pipeline.crawl(source_id)
        record("12. Full pipeline crawl", cres.get("status") == "ok",
               f"docs={len(cres.get('new_documents', []))}")

    fails = [n for n, ok, _ in RESULT if not ok]
    print("\n" + "=" * 50)
    print(f"{len(RESULT) - len(fails)}/{len(RESULT)} PASS")
    if fails:
        print("GAGAL:", ", ".join(fails))


asyncio.run(main())
