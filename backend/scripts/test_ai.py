import asyncio
import traceback

from app.modules.ai import get_ai
from app.shared.config import get_settings


async def main():
    s = get_settings()
    print("provider:", s.ai_provider)
    print("key set:", bool(s.openrouter_api_key), "len:", len(s.openrouter_api_key))
    print("model:", s.ai_chat_model)
    ai = get_ai()
    try:
        r = await ai.chat(
            messages=[{"role": "user", "content": "Balas satu kata: siap"}],
            max_tokens=10,
        )
        print("CHAT OK:", r.content[:80])
    except Exception:
        traceback.print_exc()


asyncio.run(main())
