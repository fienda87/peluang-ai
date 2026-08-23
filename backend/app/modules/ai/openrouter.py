import json
from typing import Any

import httpx

from app.modules.ai.ports import AIPort, AIProviderError, AIResponse, EmbeddingResponse
from app.shared.config import get_settings
from app.shared.logging import get_logger

logger = get_logger("ai.openrouter")


class OpenRouterAdapter(AIPort):
    def __init__(self) -> None:
        s = get_settings()
        self.base_url = s.openrouter_base_url
        self.api_key = s.openrouter_api_key
        self.chat_model = s.ai_chat_model
        self.vision_model = s.ai_vision_model
        self.embedding_model = s.ai_embedding_model
        raw = getattr(s, "ai_fallback_models", "") or ""
        self.fallback_models = [m.strip() for m in raw.split(",") if m.strip()]

    def get_model(self, purpose: str = "chat") -> str:
        if purpose == "vision":
            return self.vision_model
        if purpose == "embedding":
            return self.embedding_model
        return self.chat_model

    def _model_chain(self, model_key: str | None) -> list[str]:
        primary = model_key or self.chat_model
        return [primary] + [m for m in self.fallback_models if m != primary]

    async def chat(
        self,
        messages: list[dict[str, str]],
        model_key: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> AIResponse:
        last_error: AIProviderError | None = None
        for model in self._model_chain(model_key):
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            try:
                data = await self._post("/chat/completions", payload)
            except AIProviderError as e:
                last_error = e
                if e.code in ("PROVIDER_RATE_LIMIT", "PROVIDER_ERROR"):
                    logger.warning("model_fallback", failed=model, code=e.code)
                    continue
                raise

            usage = data.get("usage", {})
            choices = data.get("choices") or []
            if not choices:
                logger.warning("empty_choices", model=model, body=str(data)[:200])
                last_error = AIProviderError("Empty choices from provider", "PROVIDER_ERROR")
                continue
            message = choices[0].get("message", {})
            content = message.get("content")
            if content is None:
                # Reasoning models may return reasoning-only when tokens run out
                content = message.get("reasoning") or ""
            return AIResponse(
                content=content,
                model=data.get("model", model),
                tokens_used=usage.get("total_tokens", 0),
                metadata=data,
            )

        if last_error:
            raise last_error
        raise AIProviderError("No models configured", "PROVIDER_ERROR")

    async def structured_extract(
        self,
        prompt: str,
        schema: dict[str, Any],
        model_key: str | None = None,
    ) -> AIResponse:
        system = (
            "You are a structured data extraction engine. "
            "Respond ONLY with valid JSON matching this schema:\n"
            f"{json.dumps(schema)}"
        )
        response = await self.chat(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            model_key=model_key,
        )
        try:
            json.loads(response.content)
        except json.JSONDecodeError as e:
            raise AIProviderError(f"Invalid JSON from model: {e}", "SCHEMA_VALIDATION_FAILED")
        return response

    async def embed(
        self,
        texts: list[str],
        model_key: str | None = None,
    ) -> EmbeddingResponse:
        model = model_key or self.embedding_model
        payload = {"model": model, "input": texts}
        data = await self._post("/embeddings", payload)
        embeddings = [item["embedding"] for item in data["data"]]
        usage = data.get("usage", {})
        return EmbeddingResponse(
            embeddings=embeddings,
            model=model,
            tokens_used=usage.get("total_tokens", 0),
        )

    async def _post(self, path: str, payload: dict) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://peluang.ai",
            "X-Title": "Peluang.ai",
        }
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(f"{self.base_url}{path}", json=payload, headers=headers)
        except httpx.TimeoutException as e:
            raise AIProviderError(str(e), "PROVIDER_TIMEOUT")
        except httpx.HTTPError as e:
            raise AIProviderError(str(e), "NETWORK_ERROR")

        if resp.status_code == 429:
            raise AIProviderError("Rate limited", "PROVIDER_RATE_LIMIT")
        if resp.status_code >= 500:
            raise AIProviderError(f"Provider error {resp.status_code}", "PROVIDER_ERROR")
        if resp.status_code >= 400:
            raise AIProviderError(
                f"Request failed {resp.status_code}: {resp.text[:200]}", "PROVIDER_ERROR"
            )
        return resp.json()
