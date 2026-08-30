from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

CONFIG_DIR = Path(__file__).resolve().parents[3] / "config"
ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE), env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str = "postgresql+asyncpg://peluang:peluang_dev@localhost:5432/peluang"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_expire_minutes: int = 60
    jwt_refresh_expire_days: int = 30

    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    ollama_base_url: str = "http://localhost:11434"
    ollama_num_parallel: int = 1
    ollama_keep_alive: str = "-1"

    ai_provider: str = Field(default="openrouter", description="openrouter | ollama")
    ai_chat_model: str = "meta-llama/llama-3.1-8b-instruct:free"
    ai_vision_model: str = "google/gemini-flash-1.5"
    ai_embedding_model: str = "openai/text-embedding-3-small"
    ai_fallback_models: str = ""

    embedding_backend: str = "local"

    telegram_bot_token: str = ""
    web_base_url: str = "http://localhost:3000"

    storage_backend: str = "local"
    storage_local_path: str = "./data/storage"


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def _load_yaml(name: str) -> dict[str, Any]:
    path = CONFIG_DIR / name
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_app_config() -> dict[str, Any]:
    return _load_yaml("app.yaml")


def get_agent_budget(agent_name: str) -> dict[str, Any]:
    return _load_yaml("agents.yaml").get(agent_name, {})


def is_feature_enabled(name: str) -> bool:
    return bool(get_app_config().get("features", {}).get(name, False))
