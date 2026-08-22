from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AIResponse:
    content: str
    model: str
    tokens_used: int = 0
    cost_usd: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EmbeddingResponse:
    embeddings: list[list[float]]
    model: str
    tokens_used: int = 0


class AIProviderError(Exception):
    def __init__(self, message: str, code: str = "PROVIDER_ERROR") -> None:
        super().__init__(message)
        self.code = code


class AIPort(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        model_key: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> AIResponse: ...

    @abstractmethod
    async def structured_extract(
        self,
        prompt: str,
        schema: dict[str, Any],
        model_key: str | None = None,
    ) -> AIResponse: ...

    @abstractmethod
    async def embed(
        self,
        texts: list[str],
        model_key: str | None = None,
    ) -> EmbeddingResponse: ...

    @abstractmethod
    def get_model(self, purpose: str = "chat") -> str: ...
