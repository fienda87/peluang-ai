"""Hybrid AI adapter: API-first, Ollama lokal fallback terakhir.

Routing per purpose (AI_PROVIDER=auto):
- chat/extract  → OpenRouter (model chain) → Ollama → None (caller UNKNOWN)
- vision        → SELALU API (llama3.2 bukan model VL); API mati → None
- embedding     → tidak via adapter ini (EmbeddingService local MiniLM)
"""

from app.modules.ai.ollama import OllamaAdapter
from app.modules.ai.openrouter import OpenRouterAdapter
from app.modules.ai.ports import (
    AIPort,
    AIProviderError,
    AIResponse,
    EmbeddingResponse,
)
from app.shared.logging import get_logger

logger = get_logger("ai.hybrid")


class HybridAIAdapter(AIPort):
    def __init__(self) -> None:
        self.api = OpenRouterAdapter()
        self.local = OllamaAdapter()

    def get_model(self, purpose: str = "chat") -> str:
        # Vision & chat selalu dicoba API dulu
        return self.api.get_model(purpose)

    async def chat(self, messages, model_key=None, temperature=0.0, max_tokens=2048) -> AIResponse:
        # API-first
        try:
            return await self.api.chat(
                messages, model_key=model_key, temperature=temperature, max_tokens=max_tokens
            )
        except AIProviderError as e:
            logger.warning("hybrid_api_failed_fallback_local", code=e.code)

        # Multimodal (image) → Ollama tidak bisa; langsung gagal
        content = messages[-1].get("content") if messages else None
        if isinstance(content, list) and any(c.get("type") == "image" for c in content):
            raise AIProviderError("Vision API unavailable", "PROVIDER_ERROR")

        # Fallback lokal (teks saja)
        try:
            return await self.local.chat(
                messages, temperature=temperature, max_tokens=max_tokens
            )
        except AIProviderError as e:
            logger.error("hybrid_all_failed", local_error=e.code)
            raise AIProviderError("All providers failed", "PROVIDER_ERROR")

    async def structured_extract(self, prompt, schema, model_key=None) -> AIResponse:
        try:
            return await self.api.structured_extract(prompt, schema, model_key=model_key)
        except AIProviderError as e:
            logger.warning("hybrid_extract_api_failed", code=e.code)
        return await self.local.structured_extract(prompt, schema)

    async def embed(self, texts, model_key=None) -> EmbeddingResponse:
        # Embedding tidak pernah via hybrid (MiniLM lokal dipakai EmbeddingService)
        return await self.local.embed(texts, model_key)
