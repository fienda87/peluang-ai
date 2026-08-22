import json
from typing import Any

import httpx

from app.modules.ai.ports import AIPort, AIProviderError, AIResponse, EmbeddingResponse
from app.shared.config import get_settings
from app.shared.logging import get_logger

logger = get_logger("ai.ollama")

OLLAMA_CHAT_MODEL = "llama3.1:8b"
OLLAMA_EMBEDDING_MODEL = "nomic-embed-text"


class OllamaAdapter(AIPort):
    def __init__(self) -> None:
        self.base_url = get_settings().ollama_base_url

    def get_model(self, purpose: str = "chat") -> str:
        if purpose == "embedding":
            return OLLAMA_EMBEDDING_MODEL
        return OLLAMA_CHAT_MODEL

    async def chat(
        self,
        messages: list[dict[str, str]],
        model_key: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> AIResponse:
        model = model_key or OLLAMA_CHAT_MODEL
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        data = await self._post("/api/chat", payload)
        return AIResponse(
            content=data["message"]["content"],
            model=model,
            tokens_used=data.get("eval_count", 0),
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
        model = model_key or OLLAMA_EMBEDDING_MODEL
        embeddings = []
        for text in texts:
            data = await self._post("/api/embeddings", {"model": model, "prompt": text})
            embeddings.append(data["embedding"])
        return EmbeddingResponse(embeddings=embeddings, model=model)

    async def _post(self, path: str, payload: dict) -> dict:
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(f"{self.base_url}{path}", json=payload)
        except httpx.TimeoutException as e:
            raise AIProviderError(str(e), "PROVIDER_TIMEOUT")
        except httpx.HTTPError as e:
            raise AIProviderError(str(e), "NETWORK_ERROR")

        if resp.status_code >= 400:
            raise AIProviderError(
                f"Ollama error {resp.status_code}: {resp.text[:200]}", "PROVIDER_ERROR"
            )
        return resp.json()
