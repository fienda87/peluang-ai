"""Smoke: matriks 3 mode AI (auto/openrouter/ollama) — chat + vision + fallback."""
import asyncio
import os

MODES = ["auto", "openrouter", "ollama"]


async def test_chat(mode: str) -> tuple[bool, str]:
    os.environ["AI_PROVIDER"] = mode
    from app.shared.config import get_settings

    get_settings.cache_clear()
    import importlib

    import app.modules.ai as ai_mod

    importlib.reload(ai_mod)
    ai_mod.get_ai.cache_clear()
    try:
        r = await ai_mod.get_ai().chat(
            messages=[{"role": "user", "content": "Reply one word: ready"}],
            max_tokens=2000,
        )
        return True, f"model={r.model[:44]} content={r.content[:24]!r}"
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:80]}"


async def test_vision(mode: str) -> tuple[bool, str]:
    """Vision: kirim gambar 1x1 (hanya cek routing, bukan hasil)."""
    os.environ["AI_PROVIDER"] = mode
    from app.shared.config import get_settings

    get_settings.cache_clear()
    import importlib

    import app.modules.ai as ai_mod

    importlib.reload(ai_mod)
    ai_mod.get_ai.cache_clear()
    from pathlib import Path

    img = Path("tests/fixtures/image/poster_beasiswa_chevening.png").read_bytes()
    from app.modules.extraction.vision_service import VisionExtractionService

    try:
        r = await VisionExtractionService(ai_mod.get_ai()).extract_from_image(img)
        return r is not None and r.title is not None, (
            f"title={(r.title or '')[:36]!r}" if r else "returned None"
        )
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:80]}"


async def main():
    print(f"{'MODE':<12} {'CHAT':<6} {'VISION':<6} detail")
    print("-" * 80)
    for mode in MODES:
        chat_ok, chat_d = await test_chat(mode)
        vis_ok, vis_d = await test_vision(mode)
        print(
            f"{mode:<12} {'PASS' if chat_ok else 'FAIL':<6} "
            f"{'PASS' if vis_ok else 'FAIL':<6} {chat_d} | {vis_d}"
        )
    # restore
    os.environ["AI_PROVIDER"] = "auto"


asyncio.run(main())
