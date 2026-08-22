from functools import lru_cache

from app.modules.ai.ollama import OllamaAdapter
from app.modules.ai.openrouter import OpenRouterAdapter
from app.modules.ai.ports import AIPort, AIProviderError, AIResponse, EmbeddingResponse
from app.shared.config import get_settings
from app.shared.logging import get_logger

logger = get_logger("ai")

__all__ = ["AIPort", "AIProviderError", "AIResponse", "EmbeddingResponse", "get_ai"]


@lru_cache
def get_ai() -> AIPort:
    provider = get_settings().ai_provider
    if provider == "ollama":
        logger.info("ai_provider_selected", provider="ollama")
        return OllamaAdapter()
    logger.info("ai_provider_selected", provider="openrouter")
    return OpenRouterAdapter()
