import asyncio

import httpx

from app.shared.config import get_settings


async def main():
    s = get_settings()
    models = [
        "z-ai/glm-5.2:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "deepseek/deepseek-chat-v3-0324:free",
        "google/gemini-2.0-flash-exp:free",
        "qwen/qwen-2.5-72b-instruct:free",
    ]
    async with httpx.AsyncClient(timeout=60) as client:
        for m in models:
            try:
                r = await client.post(
                    f"{s.openrouter_base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {s.openrouter_api_key}"},
                    json={
                        "model": m,
                        "messages": [{"role": "user", "content": "say ready"}],
                        "max_tokens": 10,
                    },
                )
                if r.status_code == 200:
                    content = r.json()["choices"][0]["message"]["content"]
                    print(f"{m} -> OK: {content[:40]}")
                else:
                    err = r.json().get("error", {})
                    print(f"{m} -> {r.status_code}: {err.get('message', '')[:90]}")
            except Exception as e:
                print(f"{m} -> EXC: {e}")
            await asyncio.sleep(2)


asyncio.run(main())
