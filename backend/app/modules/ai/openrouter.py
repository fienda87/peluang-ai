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

    def get_model(self, purpose: str = "chat") -> str:
        if purpose == "vision":
            return self.vision_model
        if purpose == "embedding":
            return self.embedding_model
        return self.chat_model

    async def chat(
        self,
        messages: list[dict[str, str]],
        model_key: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> AIResponse:
        model = model_key or self.chat_model
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        data = await self._post("/chat/completions", payload)
        usage = data.get("usage", {})
        return AIResponse(
            content=data["choices"][0]["message"]["content"],
            model=data.get("model", model),
            tokens_used=usage.get("total_tokens", 0),
            metadata=data,
        )

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
        headers = {"Authorization": f"Bearer {self.api_key}"}
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
